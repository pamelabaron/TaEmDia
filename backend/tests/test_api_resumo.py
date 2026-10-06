"""A tela do resumo diário pela API.

Cobre a janela de 7 dias (RN-R01), o isolamento entre contas (RNF07) e a
escolha do canal de entrega.
"""
from datetime import date, timedelta

import pytest

HOJE = date.today()


def _datas(cliente_http, cabecalho, dia: date):
    return cliente_http.get(f"/relatorios/resumo?dia={dia.isoformat()}", headers=cabecalho)


class TestJanelaDeConsulta:
    def test_hoje_pode(self, cliente_http, cabecalho_auth):
        assert _datas(cliente_http, cabecalho_auth, HOJE).status_code == 200

    def test_seis_dias_atras_pode(self, cliente_http, cabecalho_auth):
        assert _datas(cliente_http, cabecalho_auth, HOJE - timedelta(days=6)).status_code == 200

    def test_sete_dias_atras_e_recusado(self, cliente_http, cabecalho_auth):
        r = _datas(cliente_http, cabecalho_auth, HOJE - timedelta(days=7))
        assert r.status_code == 422

    def test_data_futura_e_recusada(self, cliente_http, cabecalho_auth):
        r = _datas(cliente_http, cabecalho_auth, HOJE + timedelta(days=1))
        assert r.status_code == 422

    def test_sem_dia_devolve_hoje(self, cliente_http, cabecalho_auth):
        r = cliente_http.get("/relatorios/resumo", headers=cabecalho_auth)
        assert r.status_code == 200
        assert r.json()["dia"] == HOJE.isoformat()


class TestConteudo:
    def test_dia_parado_responde_sem_atividade(self, cliente_http, cabecalho_auth):
        r = _datas(cliente_http, cabecalho_auth, HOJE)
        corpo = r.json()
        assert corpo["houve_atividade"] is False
        assert corpo["cobrancas_enviadas"] == 0
        assert corpo["valor_recebido"] == 0

    def test_traz_os_dias_disponiveis_para_o_filtro(self, cliente_http, cabecalho_auth):
        """A tela precisa saber quais datas oferecer sem calcular por conta própria."""
        r = cliente_http.get("/relatorios/resumo/dias", headers=cabecalho_auth)
        assert r.status_code == 200
        dias = r.json()
        assert len(dias) == 7
        assert dias[0] == HOJE.isoformat()

    def test_exporta_em_pdf(self, cliente_http, cabecalho_auth):
        r = cliente_http.get(f"/relatorios/resumo/pdf?dia={HOJE.isoformat()}",
                             headers=cabecalho_auth)
        assert r.status_code == 200
        assert r.content.startswith(b"%PDF")

    def test_pdf_respeita_a_janela(self, cliente_http, cabecalho_auth):
        r = cliente_http.get(
            f"/relatorios/resumo/pdf?dia={(HOJE - timedelta(days=30)).isoformat()}",
            headers=cabecalho_auth)
        assert r.status_code == 422


class TestAcesso:
    def test_sem_token_recusa(self, cliente_http):
        assert cliente_http.get("/relatorios/resumo").status_code == 401

    def test_vencido_continua_consultando(self, cliente_http, cabecalho_vencido):
        """Resumo é leitura: quem venceu continua vendo o que aconteceu."""
        assert cliente_http.get("/relatorios/resumo", headers=cabecalho_vencido).status_code == 200


class TestCanalDeEntrega:
    def test_padrao_e_whatsapp(self, cliente_http, cabecalho_auth):
        r = cliente_http.get("/configuracoes", headers=cabecalho_auth)
        assert r.json()["canal_resumo"] == "whatsapp"

    def test_escolhe_email_com_endereco(self, cliente_http, cabecalho_auth):
        r = cliente_http.patch("/configuracoes",
                               json={"canal_resumo": "email", "email_resumo": "eu@exemplo.com"},
                               headers=cabecalho_auth)
        assert r.status_code == 200
        assert r.json()["canal_resumo"] == "email"
        assert r.json()["email_resumo"] == "eu@exemplo.com"

    def test_email_sem_endereco_e_recusado(self, cliente_http, cabecalho_auth):
        """Escolher e-mail sem dizer para onde deixaria o resumo sem destino."""
        r = cliente_http.patch("/configuracoes", json={"canal_resumo": "email"},
                               headers=cabecalho_auth)
        assert r.status_code == 422

    def test_endereco_invalido_e_recusado(self, cliente_http, cabecalho_auth):
        r = cliente_http.patch("/configuracoes",
                               json={"canal_resumo": "ambos", "email_resumo": "isso-nao-e-email"},
                               headers=cabecalho_auth)
        assert r.status_code == 422

    def test_canal_invalido_e_recusado(self, cliente_http, cabecalho_auth):
        r = cliente_http.patch("/configuracoes", json={"canal_resumo": "pombo"},
                               headers=cabecalho_auth)
        assert r.status_code == 422
