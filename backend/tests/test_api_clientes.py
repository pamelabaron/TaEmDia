"""Testes da API de clientes: cadastro, unicidade e isolamento entre contas."""
import uuid

import pytest

from app.core.security import criar_access_token
from app.modules.vendedores.models import Vendedor

NOVO = {"nome": "Rosangela Ferreira", "whatsapp_numero": "5547999990001"}


class TestAutenticacaoObrigatoria:
    """RN01: nenhuma funcionalidade sem estar autenticado."""

    def test_listar_sem_token_e_bloqueado(self, cliente_http):
        assert cliente_http.get("/clientes").status_code == 401

    def test_cadastrar_sem_token_e_bloqueado(self, cliente_http):
        assert cliente_http.post("/clientes", json=NOVO).status_code == 401

    def test_token_invalido_e_bloqueado(self, cliente_http):
        resp = cliente_http.get("/clientes", headers={"Authorization": "Bearer invalido"})
        assert resp.status_code == 401


class TestCadastro:
    def test_cadastra_e_lista(self, cliente_http, cabecalho_auth):
        criado = cliente_http.post("/clientes", json=NOVO, headers=cabecalho_auth)
        assert criado.status_code == 201
        assert criado.json()["nome"] == NOVO["nome"]

        lista = cliente_http.get("/clientes", headers=cabecalho_auth).json()
        assert len(lista) == 1
        assert lista[0]["whatsapp_numero"] == NOVO["whatsapp_numero"]

    def test_campos_opcionais(self, cliente_http, cabecalho_auth):
        dados = {**NOVO, "cpf": "12345678900", "endereco": "Rua A, 100"}
        resp = cliente_http.post("/clientes", json=dados, headers=cabecalho_auth)
        assert resp.json()["cpf"] == "12345678900"
        assert resp.json()["endereco"] == "Rua A, 100"

    def test_novo_cliente_ja_vem_com_envio_automatico_ligado(self, cliente_http, cabecalho_auth):
        resp = cliente_http.post("/clientes", json=NOVO, headers=cabecalho_auth)
        assert resp.json()["envio_auto_ativo"] is True
        assert resp.json()["interacao_habilitada"] is True

    def test_whatsapp_duplicado_e_recusado(self, cliente_http, cabecalho_auth):
        """RF05/RN04: um número não pode se repetir na mesma conta."""
        cliente_http.post("/clientes", json=NOVO, headers=cabecalho_auth)
        repetido = cliente_http.post("/clientes", json=NOVO, headers=cabecalho_auth)
        assert repetido.status_code == 409
        assert "WhatsApp" in repetido.json()["detail"]

    def test_nome_obrigatorio(self, cliente_http, cabecalho_auth):
        resp = cliente_http.post("/clientes", json={"whatsapp_numero": "5547999990002"},
                                 headers=cabecalho_auth)
        assert resp.status_code == 422


class TestEdicaoERemocao:
    def _criar(self, cliente_http, cabecalho_auth):
        return cliente_http.post("/clientes", json=NOVO, headers=cabecalho_auth).json()["id"]

    def test_edita_dados(self, cliente_http, cabecalho_auth):
        cid = self._criar(cliente_http, cabecalho_auth)
        resp = cliente_http.patch(f"/clientes/{cid}", json={"nome": "Rosangela F. Silva"},
                                  headers=cabecalho_auth)
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Rosangela F. Silva"

    def test_desliga_envio_automatico_do_cliente(self, cliente_http, cabecalho_auth):
        cid = self._criar(cliente_http, cabecalho_auth)
        resp = cliente_http.patch(f"/clientes/{cid}", json={"envio_auto_ativo": False},
                                  headers=cabecalho_auth)
        assert resp.json()["envio_auto_ativo"] is False

    def test_remover_e_soft_delete(self, cliente_http, cabecalho_auth):
        """Desativar preserva o histórico: o cliente some da lista, mas não do banco."""
        cid = self._criar(cliente_http, cabecalho_auth)
        assert cliente_http.delete(f"/clientes/{cid}", headers=cabecalho_auth).status_code == 204
        assert cliente_http.get("/clientes", headers=cabecalho_auth).json() == []

    def test_cliente_inexistente_retorna_404(self, cliente_http, cabecalho_auth):
        resp = cliente_http.patch(f"/clientes/{uuid.uuid4()}", json={"nome": "X"},
                                  headers=cabecalho_auth)
        assert resp.status_code == 404


class TestIsolamentoEntreContas:
    """RNF07/RN02: cada vendedor só enxerga os próprios dados."""

    def test_cliente_de_outro_vendedor_nao_aparece(self, cliente_http, cabecalho_auth, db):
        cliente_http.post("/clientes", json=NOVO, headers=cabecalho_auth)

        outro = Vendedor(google_email="outro@exemplo.com", nome="Outro")
        db.add(outro)
        db.commit()
        db.refresh(outro)
        cabecalho_outro = {"Authorization": f"Bearer {criar_access_token(outro.id)}"}

        assert cliente_http.get("/clientes", headers=cabecalho_outro).json() == []

    def test_mesmo_numero_pode_existir_em_contas_diferentes(self, cliente_http, cabecalho_auth, db):
        cliente_http.post("/clientes", json=NOVO, headers=cabecalho_auth)

        outro = Vendedor(google_email="outro2@exemplo.com", nome="Outro 2")
        db.add(outro)
        db.commit()
        db.refresh(outro)
        cabecalho_outro = {"Authorization": f"Bearer {criar_access_token(outro.id)}"}

        resp = cliente_http.post("/clientes", json=NOVO, headers=cabecalho_outro)
        assert resp.status_code == 201

    def test_nao_edita_cliente_de_outra_conta(self, cliente_http, cabecalho_auth, db):
        cid = cliente_http.post("/clientes", json=NOVO, headers=cabecalho_auth).json()["id"]

        outro = Vendedor(google_email="outro3@exemplo.com", nome="Outro 3")
        db.add(outro)
        db.commit()
        db.refresh(outro)
        cabecalho_outro = {"Authorization": f"Bearer {criar_access_token(outro.id)}"}

        resp = cliente_http.patch(f"/clientes/{cid}", json={"nome": "Invadido"},
                                  headers=cabecalho_outro)
        assert resp.status_code == 404
