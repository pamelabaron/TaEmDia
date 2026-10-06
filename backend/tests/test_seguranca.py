"""Testes dos controles de segurança (checklist pré-deploy do Marco M4)."""
import pytest

from app.core.config import JWT_SECRET_PADRAO, Settings


class TestProtecaoDoWebhook:
    """O webhook não usa JWT (quem chama é o serviço de WhatsApp), então é
    protegido por um segredo compartilhado."""

    CORPO = {"numero": "5547999990001", "texto": "1"}

    def test_sem_token_configurado_o_webhook_fica_aberto_em_desenvolvimento(
        self, cliente_http, monkeypatch
    ):
        from app.core.config import settings

        monkeypatch.setattr(settings, "WEBHOOK_TOKEN", "")
        monkeypatch.setattr(settings, "AMBIENTE", "desenvolvimento")
        resp = cliente_http.post("/whatsapp/webhook", json=self.CORPO)
        assert resp.status_code == 200

    def test_com_token_configurado_recusa_quem_nao_apresenta_o_segredo(
        self, cliente_http, monkeypatch
    ):
        from app.core.config import settings

        monkeypatch.setattr(settings, "WEBHOOK_TOKEN", "segredo-do-webhook")
        resp = cliente_http.post("/whatsapp/webhook", json=self.CORPO)
        assert resp.status_code == 401

    def test_recusa_token_errado(self, cliente_http, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "WEBHOOK_TOKEN", "segredo-do-webhook")
        resp = cliente_http.post("/whatsapp/webhook", json=self.CORPO,
                                 headers={"X-Webhook-Token": "errado"})
        assert resp.status_code == 401

    def test_aceita_o_segredo_pelo_cabecalho(self, cliente_http, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "WEBHOOK_TOKEN", "segredo-do-webhook")
        resp = cliente_http.post("/whatsapp/webhook", json=self.CORPO,
                                 headers={"X-Webhook-Token": "segredo-do-webhook"})
        assert resp.status_code == 200

    def test_aceita_o_segredo_pela_url(self, cliente_http, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "WEBHOOK_TOKEN", "segredo-do-webhook")
        resp = cliente_http.post("/whatsapp/webhook?token=segredo-do-webhook",
                                 json=self.CORPO)
        assert resp.status_code == 200

    def test_em_producao_sem_token_o_webhook_fica_desabilitado(
        self, cliente_http, monkeypatch
    ):
        from app.core.config import settings

        monkeypatch.setattr(settings, "WEBHOOK_TOKEN", "")
        monkeypatch.setattr(settings, "AMBIENTE", "producao")
        resp = cliente_http.post("/whatsapp/webhook", json=self.CORPO)
        assert resp.status_code == 503


class TestValidacaoDeProducao:
    """A aplicação se recusa a subir em produção com configuração insegura."""

    def _config(self, **extra):
        base = dict(
            AMBIENTE="producao",
            JWT_SECRET="x" * 40,
            DATABASE_URL="postgresql+psycopg://taemdia:senha-forte@db:5432/taemdia",
            WEBHOOK_TOKEN="segredo",
            GOOGLE_CLIENT_ID="id",
            GOOGLE_CLIENT_SECRET="segredo",
            FRONTEND_URL="https://taemdia.exemplo.com",
        )
        base.update(extra)
        return Settings(**base)

    def test_configuracao_correta_nao_acusa_problemas(self):
        assert self._config().validar_para_producao() == []

    def test_acusa_jwt_secret_padrao(self):
        problemas = self._config(JWT_SECRET=JWT_SECRET_PADRAO).validar_para_producao()
        assert any("JWT_SECRET" in p for p in problemas)

    def test_acusa_jwt_secret_curto(self):
        problemas = self._config(JWT_SECRET="curto").validar_para_producao()
        assert any("JWT_SECRET" in p for p in problemas)

    def test_acusa_senha_padrao_do_banco(self):
        problemas = self._config(
            DATABASE_URL="postgresql+psycopg://taemdia:troque_esta_senha@db:5432/taemdia"
        ).validar_para_producao()
        assert any("banco" in p for p in problemas)

    def test_acusa_webhook_sem_token(self):
        problemas = self._config(WEBHOOK_TOKEN="").validar_para_producao()
        assert any("WEBHOOK_TOKEN" in p for p in problemas)

    def test_acusa_google_nao_configurado(self):
        problemas = self._config(GOOGLE_CLIENT_ID="").validar_para_producao()
        assert any("Google" in p for p in problemas)

    def test_acusa_frontend_sem_https(self):
        problemas = self._config(FRONTEND_URL="http://taemdia.exemplo.com").validar_para_producao()
        assert any("HTTPS" in p for p in problemas)

    def test_em_desenvolvimento_nao_e_producao(self):
        assert Settings(AMBIENTE="desenvolvimento").em_producao is False
        assert Settings(AMBIENTE="producao").em_producao is True


class TestCorsConfiguravel:
    def test_uma_origem(self):
        s = Settings(FRONTEND_URL="https://app.exemplo.com")
        assert s.origens_permitidas == ["https://app.exemplo.com"]

    def test_varias_origens_separadas_por_virgula(self):
        s = Settings(FRONTEND_URL="https://a.com, https://b.com")
        assert s.origens_permitidas == ["https://a.com", "https://b.com"]

    def test_ignora_entradas_vazias(self):
        s = Settings(FRONTEND_URL="https://a.com,,  ")
        assert s.origens_permitidas == ["https://a.com"]


class TestSegredosDeExemplo:
    """Os valores de exemplo do .env.example nunca podem passar em produção."""

    def _config(self, **extra):
        base = dict(
            AMBIENTE="producao",
            JWT_SECRET="x" * 40,
            DATABASE_URL="postgresql+psycopg://taemdia:senha-forte@db:5432/taemdia",
            WEBHOOK_TOKEN="segredo",
            GOOGLE_CLIENT_ID="id",
            GOOGLE_CLIENT_SECRET="segredo",
            FRONTEND_URL="https://taemdia.exemplo.com",
        )
        base.update(extra)
        return Settings(**base)

    def test_recusa_o_texto_de_exemplo_do_jwt(self):
        """Esse texto tem 40 caracteres e passaria só pela checagem de tamanho."""
        problemas = self._config(
            JWT_SECRET="gere_uma_chave_secreta_longa_e_aleatoria"
        ).validar_para_producao()
        assert any("JWT_SECRET" in p for p in problemas)

    def test_recusa_valor_de_exemplo_no_webhook(self):
        problemas = self._config(WEBHOOK_TOKEN="troque-esta-chave").validar_para_producao()
        assert any("WEBHOOK_TOKEN" in p for p in problemas)

    def test_acumula_todos_os_problemas_de_uma_vez(self):
        """A mensagem de erro deve apontar tudo o que falta, não só o primeiro item."""
        problemas = Settings(AMBIENTE="producao").validar_para_producao()
        assert len(problemas) >= 3
