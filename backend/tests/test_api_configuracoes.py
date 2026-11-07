"""Testes das configurações do agente de cobrança."""
import pytest


class TestConfiguracoes:
    def test_exige_autenticacao(self, cliente_http):
        assert cliente_http.get("/configuracoes").status_code == 401

    def test_primeira_consulta_cria_os_padroes(self, cliente_http, cabecalho_auth):
        c = cliente_http.get("/configuracoes", headers=cabecalho_auth).json()
        assert c["dias_antecedencia_lembrete"] == 3
        assert c["horario_resumo"] == "20:00:00"
        assert c["resumo_ativo"] is True
        assert c["envio_auto_global"] is True

    def test_consultas_seguintes_reaproveitam_o_mesmo_registro(self, cliente_http, cabecalho_auth):
        primeira = cliente_http.get("/configuracoes", headers=cabecalho_auth).json()
        segunda = cliente_http.get("/configuracoes", headers=cabecalho_auth).json()
        assert primeira["id"] == segunda["id"]

    def test_altera_e_persiste(self, cliente_http, cabecalho_auth):
        cliente_http.patch("/configuracoes", headers=cabecalho_auth,
                           json={"dias_antecedencia_lembrete": 7, "horario_resumo": "19:00:00"})
        atual = cliente_http.get("/configuracoes", headers=cabecalho_auth).json()
        assert atual["dias_antecedencia_lembrete"] == 7
        assert atual["horario_resumo"] == "19:00:00"

    def test_alteracao_parcial_nao_apaga_os_outros_campos(self, cliente_http, cabecalho_auth):
        cliente_http.patch("/configuracoes", headers=cabecalho_auth,
                           json={"dias_antecedencia_lembrete": 5})
        atual = cliente_http.get("/configuracoes", headers=cabecalho_auth).json()
        assert atual["dias_antecedencia_lembrete"] == 5
        assert atual["horario_resumo"] == "20:00:00"

    def test_desliga_envio_automatico(self, cliente_http, cabecalho_auth):
        resp = cliente_http.patch("/configuracoes", headers=cabecalho_auth,
                                  json={"envio_auto_global": False})
        assert resp.json()["envio_auto_global"] is False

    def test_desliga_resumo_diario(self, cliente_http, cabecalho_auth):
        resp = cliente_http.patch("/configuracoes", headers=cabecalho_auth,
                                  json={"resumo_ativo": False})
        assert resp.json()["resumo_ativo"] is False

    @pytest.mark.parametrize("dias", [-1, 31, 100])
    def test_dias_fora_da_faixa_sao_recusados(self, cliente_http, cabecalho_auth, dias):
        resp = cliente_http.patch("/configuracoes", headers=cabecalho_auth,
                                  json={"dias_antecedencia_lembrete": dias})
        assert resp.status_code == 422

    @pytest.mark.parametrize("dias", [0, 15, 30])
    def test_limites_validos_sao_aceitos(self, cliente_http, cabecalho_auth, dias):
        resp = cliente_http.patch("/configuracoes", headers=cabecalho_auth,
                                  json={"dias_antecedencia_lembrete": dias})
        assert resp.status_code == 200
