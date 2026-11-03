"""Testes do painel financeiro e do ranking."""
from datetime import date, timedelta

import pytest

HOJE = date.today()


@pytest.fixture()
def cliente_com_venda(cliente_http, cabecalho_auth):
    cid = cliente_http.post("/clientes", headers=cabecalho_auth,
                            json={"nome": "Ana", "whatsapp_numero": "5547999990009"}).json()["id"]
    venda = cliente_http.post("/vendas", headers=cabecalho_auth, json={
        "cliente_id": cid, "valor_total": 300, "num_parcelas": 3,
        "data_primeira_parcela": str(HOJE - timedelta(days=40)),
    }).json()
    return {"cliente_id": cid, "venda": venda}


class TestDashboard:
    def test_exige_autenticacao(self, cliente_http):
        assert cliente_http.get("/relatorios/dashboard").status_code == 401

    def test_conta_nova_vem_zerada(self, cliente_http, cabecalho_auth):
        d = cliente_http.get("/relatorios/dashboard", headers=cabecalho_auth).json()
        assert d["total_a_receber"] == 0
        assert d["clientes_inadimplentes"] == 0
        assert d["clientes_em_atraso"] == []

    def test_total_a_receber_soma_as_parcelas_em_aberto(self, cliente_http, cabecalho_auth,
                                                        cliente_com_venda):
        d = cliente_http.get("/relatorios/dashboard", headers=cabecalho_auth).json()
        assert d["total_a_receber"] == 300.0

    def test_pagamento_move_de_a_receber_para_recebido(self, cliente_http, cabecalho_auth,
                                                       cliente_com_venda):
        pid = cliente_com_venda["venda"]["parcelas"][0]["id"]
        cliente_http.post(f"/parcelas/{pid}/pagar", headers=cabecalho_auth)
        d = cliente_http.get("/relatorios/dashboard", headers=cabecalho_auth).json()
        assert d["total_a_receber"] == 200.0
        assert d["recebido_no_mes"] == 100.0

    def test_parcelas_vencidas_entram_em_atraso(self, cliente_http, cabecalho_auth,
                                                cliente_com_venda):
        d = cliente_http.get("/relatorios/dashboard", headers=cabecalho_auth).json()
        assert d["em_atraso"] > 0
        assert d["clientes_inadimplentes"] == 1
        assert d["clientes_em_atraso"][0]["nome"] == "Ana"

    def test_venda_cancelada_sai_do_total(self, cliente_http, cabecalho_auth, cliente_com_venda):
        cliente_http.post(f"/vendas/{cliente_com_venda['venda']['id']}/cancelar",
                          headers=cabecalho_auth)
        d = cliente_http.get("/relatorios/dashboard", headers=cabecalho_auth).json()
        assert d["total_a_receber"] == 0


class TestRanking:
    def test_exige_autenticacao(self, cliente_http):
        assert cliente_http.get("/relatorios/ranking").status_code == 401

    def test_conta_sem_clientes(self, cliente_http, cabecalho_auth):
        r = cliente_http.get("/relatorios/ranking", headers=cabecalho_auth).json()
        assert r["clientes"] == []
        assert r["bons"] == 0

    def test_cliente_novo_fica_sem_historico(self, cliente_http, cabecalho_auth):
        cliente_http.post("/clientes", headers=cabecalho_auth,
                          json={"nome": "Novo", "whatsapp_numero": "5547999990010"})
        r = cliente_http.get("/relatorios/ranking", headers=cabecalho_auth).json()
        assert r["sem_historico"] == 1
        assert r["clientes"][0]["classificacao"] == "sem_historico"

    def test_parcelas_vencidas_tornam_o_cliente_inadimplente(self, cliente_http, cabecalho_auth,
                                                             cliente_com_venda):
        r = cliente_http.get("/relatorios/ranking", headers=cabecalho_auth).json()
        assert r["inadimplentes"] == 1
        assert r["clientes"][0]["classificacao"] == "inadimplente"

    def test_aceita_filtro_de_periodo(self, cliente_http, cabecalho_auth, cliente_com_venda):
        resp = cliente_http.get("/relatorios/ranking?meses=6", headers=cabecalho_auth)
        assert resp.status_code == 200
