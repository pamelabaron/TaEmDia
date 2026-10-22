"""Testes da API de vendas e parcelas (RN06, RN07, RF12, RF16)."""
import uuid
from datetime import date, timedelta

import pytest

HOJE = date.today()


@pytest.fixture()
def cliente_id(cliente_http, cabecalho_auth):
    resp = cliente_http.post(
        "/clientes", json={"nome": "Cliente Teste", "whatsapp_numero": "5547999990001"},
        headers=cabecalho_auth,
    )
    return resp.json()["id"]


def venda_payload(cliente_id, **extra):
    dados = {
        "cliente_id": cliente_id,
        "valor_total": 300,
        "num_parcelas": 3,
        "data_primeira_parcela": str(HOJE),
    }
    dados.update(extra)
    return dados


class TestRegistroDeVenda:
    def test_cria_venda_com_cronograma(self, cliente_http, cabecalho_auth, cliente_id):
        resp = cliente_http.post("/vendas", json=venda_payload(cliente_id), headers=cabecalho_auth)
        assert resp.status_code == 201
        venda = resp.json()
        assert len(venda["parcelas"]) == 3
        assert [p["valor"] for p in venda["parcelas"]] == [100.0, 100.0, 100.0]

    def test_vencimentos_sao_mensais(self, cliente_http, cabecalho_auth, cliente_id):
        primeira = date(2026, 1, 10)
        resp = cliente_http.post(
            "/vendas", json=venda_payload(cliente_id, data_primeira_parcela=str(primeira)),
            headers=cabecalho_auth,
        )
        vencimentos = [p["data_vencimento"] for p in resp.json()["parcelas"]]
        assert vencimentos == ["2026-01-10", "2026-02-10", "2026-03-10"]

    def test_venda_a_vista(self, cliente_http, cabecalho_auth, cliente_id):
        resp = cliente_http.post(
            "/vendas", json=venda_payload(cliente_id, num_parcelas=1), headers=cabecalho_auth,
        )
        assert len(resp.json()["parcelas"]) == 1
        assert resp.json()["parcelas"][0]["valor"] == 300.0

    def test_parcelas_comecam_pendentes(self, cliente_http, cabecalho_auth, cliente_id):
        resp = cliente_http.post(
            "/vendas", json=venda_payload(cliente_id, data_primeira_parcela=str(HOJE + timedelta(days=5))),
            headers=cabecalho_auth,
        )
        assert all(p["status"] == "pendente" for p in resp.json()["parcelas"])

    def test_parcela_vencida_aparece_como_atrasada(self, cliente_http, cabecalho_auth, cliente_id):
        resp = cliente_http.post(
            "/vendas", json=venda_payload(cliente_id, num_parcelas=1,
                                          data_primeira_parcela=str(HOJE - timedelta(days=5))),
            headers=cabecalho_auth,
        )
        assert resp.json()["parcelas"][0]["status"] == "atrasada"


class TestValidacoes:
    @pytest.mark.parametrize("valor", [0, -10])
    def test_valor_invalido_e_recusado(self, cliente_http, cabecalho_auth, cliente_id, valor):
        """RN06: o valor mínimo de uma venda é R$ 1,00."""
        resp = cliente_http.post("/vendas", json=venda_payload(cliente_id, valor_total=valor),
                                 headers=cabecalho_auth)
        assert resp.status_code == 422

    @pytest.mark.parametrize("n", [0, 61, -1])
    def test_numero_de_parcelas_fora_da_faixa(self, cliente_http, cabecalho_auth, cliente_id, n):
        """RN07: entre 1 e 60 parcelas."""
        resp = cliente_http.post("/vendas", json=venda_payload(cliente_id, num_parcelas=n),
                                 headers=cabecalho_auth)
        assert resp.status_code == 422

    def test_limite_de_60_parcelas_e_aceito(self, cliente_http, cabecalho_auth, cliente_id):
        resp = cliente_http.post("/vendas", json=venda_payload(cliente_id, num_parcelas=60,
                                                               valor_total=6000),
                                 headers=cabecalho_auth)
        assert resp.status_code == 201
        assert len(resp.json()["parcelas"]) == 60

    def test_cliente_inexistente(self, cliente_http, cabecalho_auth):
        resp = cliente_http.post("/vendas", json=venda_payload(str(uuid.uuid4())),
                                 headers=cabecalho_auth)
        assert resp.status_code in (400, 404)

    def test_sem_token(self, cliente_http, cliente_id):
        assert cliente_http.post("/vendas", json=venda_payload(cliente_id)).status_code == 401


class TestPagamentoECancelamento:
    def _venda(self, cliente_http, cabecalho_auth, cliente_id):
        return cliente_http.post("/vendas", json=venda_payload(cliente_id),
                                 headers=cabecalho_auth).json()

    def test_marcar_parcela_como_paga(self, cliente_http, cabecalho_auth, cliente_id):
        venda = self._venda(cliente_http, cabecalho_auth, cliente_id)
        pid = venda["parcelas"][0]["id"]
        resp = cliente_http.post(f"/parcelas/{pid}/pagar", headers=cabecalho_auth)
        assert resp.status_code == 200

        perfil = cliente_http.get(f"/clientes/{cliente_id}/perfil", headers=cabecalho_auth).json()
        parcela = perfil["vendas"][0]["parcelas"][0]
        assert parcela["status"] == "paga"
        assert parcela["data_pagamento"] is not None

    def test_pagamento_reduz_o_saldo_devedor(self, cliente_http, cabecalho_auth, cliente_id):
        venda = self._venda(cliente_http, cabecalho_auth, cliente_id)
        antes = cliente_http.get(f"/clientes/{cliente_id}/perfil", headers=cabecalho_auth).json()
        assert antes["saldo_devedor"] == 300.0

        cliente_http.post(f"/parcelas/{venda['parcelas'][0]['id']}/pagar", headers=cabecalho_auth)
        depois = cliente_http.get(f"/clientes/{cliente_id}/perfil", headers=cabecalho_auth).json()
        assert depois["saldo_devedor"] == 200.0

    def test_parcela_inexistente(self, cliente_http, cabecalho_auth):
        resp = cliente_http.post(f"/parcelas/{uuid.uuid4()}/pagar", headers=cabecalho_auth)
        assert resp.status_code == 404

    def test_cancelar_venda(self, cliente_http, cabecalho_auth, cliente_id):
        """RF16: venda cancelada sai do saldo devedor."""
        venda = self._venda(cliente_http, cabecalho_auth, cliente_id)
        resp = cliente_http.post(f"/vendas/{venda['id']}/cancelar", headers=cabecalho_auth)
        assert resp.status_code == 200

        perfil = cliente_http.get(f"/clientes/{cliente_id}/perfil", headers=cabecalho_auth).json()
        assert perfil["saldo_devedor"] == 0.0
        assert perfil["vendas"][0]["status"] == "cancelada"


class TestPerfilDoCliente:
    def test_perfil_sem_vendas(self, cliente_http, cabecalho_auth, cliente_id):
        perfil = cliente_http.get(f"/clientes/{cliente_id}/perfil", headers=cabecalho_auth).json()
        assert perfil["saldo_devedor"] == 0.0
        assert perfil["vendas"] == []

    def test_perfil_de_cliente_inexistente(self, cliente_http, cabecalho_auth):
        resp = cliente_http.get(f"/clientes/{uuid.uuid4()}/perfil", headers=cabecalho_auth)
        assert resp.status_code == 404
