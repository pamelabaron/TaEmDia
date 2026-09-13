"""Comportamento da assinatura pela API.

O ponto central: quem venceu **continua lendo** e **não consegue gravar** — e
isso vale mesmo chamando o endpoint direto, sem passar pela interface.
"""
import io
import uuid
from datetime import date, timedelta

import pytest

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
PDF = b"%PDF-1.4" + b"0" * 64


def _arquivo(conteudo: bytes = PNG, nome: str = "comprovante.png"):
    return {"arquivo": (nome, io.BytesIO(conteudo), "image/png")}


class TestLeituraContinuaLiberada:
    """Vencer bloqueia a escrita, não a navegação."""

    def test_vencido_le_o_painel(self, cliente_http, cabecalho_vencido):
        r = cliente_http.get("/relatorios/dashboard", headers=cabecalho_vencido)
        assert r.status_code == 200

    def test_vencido_le_a_lista_de_clientes(self, cliente_http, cabecalho_vencido):
        r = cliente_http.get("/clientes", headers=cabecalho_vencido)
        assert r.status_code == 200

    def test_vencido_le_o_ranking(self, cliente_http, cabecalho_vencido):
        r = cliente_http.get("/relatorios/ranking?meses=12", headers=cabecalho_vencido)
        assert r.status_code == 200

    def test_vencido_ve_a_propria_assinatura(self, cliente_http, cabecalho_vencido):
        """Quem venceu é justamente quem precisa dessa tela."""
        r = cliente_http.get("/assinatura", headers=cabecalho_vencido)
        assert r.status_code == 200
        assert r.json()["situacao"] == "vencida"


class TestEscritaBloqueada:
    """402 em cada endpoint que grava."""

    def test_nao_cadastra_cliente(self, cliente_http, cabecalho_vencido):
        r = cliente_http.post(
            "/clientes",
            json={"nome": "Fulano", "whatsapp_numero": "5547999990000"},
            headers=cabecalho_vencido,
        )
        assert r.status_code == 402
        assert "assinatura" in r.json()["detail"].lower()

    def test_nao_registra_venda(self, cliente_http, cabecalho_vencido):
        r = cliente_http.post(
            "/vendas",
            json={
                "cliente_id": str(uuid.uuid4()),
                "valor_total": 100,
                "num_parcelas": 2,
                "data_primeira_parcela": str(date.today()),
            },
            headers=cabecalho_vencido,
        )
        assert r.status_code == 402

    def test_nao_altera_configuracoes(self, cliente_http, cabecalho_vencido):
        r = cliente_http.patch(
            "/configuracoes", json={"envio_auto_ativo": False}, headers=cabecalho_vencido
        )
        assert r.status_code == 402

    def test_nao_conecta_whatsapp(self, cliente_http, cabecalho_vencido):
        """Ver o QR Code é conectar o WhatsApp — fica atrás da assinatura."""
        r = cliente_http.get("/whatsapp/status", headers=cabecalho_vencido)
        assert r.status_code == 402

    def test_nao_dispara_cobranca(self, cliente_http, cabecalho_vencido):
        r = cliente_http.post(
            f"/cobrancas/{uuid.uuid4()}/disparar", headers=cabecalho_vencido
        )
        assert r.status_code == 402

    def test_bloqueio_vem_antes_da_validacao(self, cliente_http, cabecalho_vencido):
        """Mesmo com dados inválidos, responde 402 — nada chega ao serviço."""
        r = cliente_http.post("/clientes", json={"nome": ""}, headers=cabecalho_vencido)
        assert r.status_code == 402


class TestQuemTemAcessoGrava:
    def test_em_teste_cadastra_normalmente(self, cliente_http, cabecalho_auth):
        r = cliente_http.post(
            "/clientes",
            json={"nome": "Cliente Novo", "whatsapp_numero": "5547988887777"},
            headers=cabecalho_auth,
        )
        assert r.status_code == 201

    def test_situacao_em_teste(self, cliente_http, cabecalho_auth):
        r = cliente_http.get("/assinatura", headers=cabecalho_auth)
        assert r.json()["situacao"] == "em_teste"


class TestEnvioDeComprovante:
    def test_vencido_consegue_enviar(self, cliente_http, cabecalho_vencido):
        """É o caminho de volta: precisa funcionar justamente para quem venceu."""
        r = cliente_http.post(
            "/assinatura/comprovante",
            data={"valor": "19.90"},
            files=_arquivo(),
            headers=cabecalho_vencido,
        )
        assert r.status_code == 201
        assert r.json()["situacao"] == "pendente"

    def test_recusa_segundo_envio_pendente(self, cliente_http, cabecalho_vencido):
        """RN-A04 — um comprovante em análise por vez."""
        cliente_http.post("/assinatura/comprovante", data={"valor": "19.90"},
                          files=_arquivo(), headers=cabecalho_vencido)
        r = cliente_http.post("/assinatura/comprovante", data={"valor": "19.90"},
                              files=_arquivo(), headers=cabecalho_vencido)
        assert r.status_code == 409

    def test_recusa_tipo_nao_aceito(self, cliente_http, cabecalho_vencido):
        """Renomear um executável para .png não engana a verificação de conteúdo."""
        r = cliente_http.post(
            "/assinatura/comprovante",
            data={"valor": "19.90"},
            files={"arquivo": ("comprovante.png", io.BytesIO(b"MZ\x90\x00nao e imagem"),
                               "image/png")},
            headers=cabecalho_vencido,
        )
        assert r.status_code == 422

    def test_recusa_arquivo_grande(self, cliente_http, cabecalho_vencido):
        grande = b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024 + 10)
        r = cliente_http.post(
            "/assinatura/comprovante",
            data={"valor": "19.90"},
            files={"arquivo": ("g.png", io.BytesIO(grande), "image/png")},
            headers=cabecalho_vencido,
        )
        assert r.status_code == 422

    def test_aceita_pdf(self, cliente_http, cabecalho_vencido):
        r = cliente_http.post(
            "/assinatura/comprovante",
            data={"valor": "19.90"},
            files={"arquivo": ("c.pdf", io.BytesIO(PDF), "application/pdf")},
            headers=cabecalho_vencido,
        )
        assert r.status_code == 201

    def test_recusa_valor_zero(self, cliente_http, cabecalho_vencido):
        r = cliente_http.post("/assinatura/comprovante", data={"valor": "0"},
                              files=_arquivo(), headers=cabecalho_vencido)
        assert r.status_code == 422


class TestAcessoDeAdministradora:
    def test_nao_admin_leva_403_na_fila(self, cliente_http, cabecalho_auth):
        r = cliente_http.get("/admin/comprovantes", headers=cabecalho_auth)
        assert r.status_code == 403

    def test_nao_admin_leva_403_ao_aprovar(self, cliente_http, cabecalho_auth):
        r = cliente_http.post(
            f"/admin/comprovantes/{uuid.uuid4()}/aprovar", headers=cabecalho_auth
        )
        assert r.status_code == 403

    def test_nao_admin_leva_403_no_download(self, cliente_http, cabecalho_auth):
        r = cliente_http.get(
            f"/admin/comprovantes/{uuid.uuid4()}/arquivo", headers=cabecalho_auth
        )
        assert r.status_code == 403

    def test_sem_token_leva_401(self, cliente_http):
        assert cliente_http.get("/admin/comprovantes").status_code == 401


class TestAprovacao:
    @pytest.fixture()
    def admin(self, db, monkeypatch):
        from app.core.config import settings
        from tests.conftest import _criar_vendedor

        v = _criar_vendedor(db, "admin@exemplo.com", "Admin", dias_de_acesso=7)
        monkeypatch.setattr(settings, "ADMIN_EMAILS", "admin@exemplo.com")
        return v

    @pytest.fixture()
    def cabecalho_admin(self, admin):
        from app.core.security import criar_access_token

        return {"Authorization": f"Bearer {criar_access_token(admin.id)}"}

    def _enviar(self, cliente_http, cabecalho):
        return cliente_http.post("/assinatura/comprovante", data={"valor": "19.90"},
                                 files=_arquivo(), headers=cabecalho).json()

    def test_aprovar_libera_a_escrita(self, cliente_http, cabecalho_vencido, cabecalho_admin):
        """O caminho completo: vencido → envia → admin aprova → volta a gravar."""
        bloqueado = cliente_http.post(
            "/clientes", json={"nome": "A", "whatsapp_numero": "5547911110000"},
            headers=cabecalho_vencido)
        assert bloqueado.status_code == 402

        pagamento = self._enviar(cliente_http, cabecalho_vencido)
        r = cliente_http.post(f"/admin/comprovantes/{pagamento['id']}/aprovar",
                              headers=cabecalho_admin)
        assert r.status_code == 200
        assert r.json()["situacao"] == "aprovado"

        liberado = cliente_http.post(
            "/clientes", json={"nome": "A", "whatsapp_numero": "5547911110000"},
            headers=cabecalho_vencido)
        assert liberado.status_code == 201

    def test_aprovar_da_trinta_dias(self, cliente_http, cabecalho_vencido, cabecalho_admin):
        pagamento = self._enviar(cliente_http, cabecalho_vencido)
        cliente_http.post(f"/admin/comprovantes/{pagamento['id']}/aprovar",
                          headers=cabecalho_admin)
        r = cliente_http.get("/assinatura", headers=cabecalho_vencido)
        assert r.json()["situacao"] == "ativa"
        assert r.json()["valido_ate"] == str(date.today() + timedelta(days=30))

    def test_recusar_nao_libera(self, cliente_http, cabecalho_vencido, cabecalho_admin):
        pagamento = self._enviar(cliente_http, cabecalho_vencido)
        r = cliente_http.post(f"/admin/comprovantes/{pagamento['id']}/recusar",
                              json={"motivo": "Comprovante ilegível."},
                              headers=cabecalho_admin)
        assert r.status_code == 200
        bloqueado = cliente_http.post(
            "/clientes", json={"nome": "A", "whatsapp_numero": "5547911110000"},
            headers=cabecalho_vencido)
        assert bloqueado.status_code == 402

    def test_nao_avalia_duas_vezes(self, cliente_http, cabecalho_vencido, cabecalho_admin):
        pagamento = self._enviar(cliente_http, cabecalho_vencido)
        cliente_http.post(f"/admin/comprovantes/{pagamento['id']}/aprovar",
                          headers=cabecalho_admin)
        r = cliente_http.post(f"/admin/comprovantes/{pagamento['id']}/aprovar",
                              headers=cabecalho_admin)
        assert r.status_code == 409

    def test_fila_mostra_o_pendente(self, cliente_http, cabecalho_vencido, cabecalho_admin):
        self._enviar(cliente_http, cabecalho_vencido)
        r = cliente_http.get("/admin/comprovantes", headers=cabecalho_admin)
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["vendedor_email"] == "vencido@exemplo.com"
