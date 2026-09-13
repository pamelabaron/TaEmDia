"""Testes das regras de vigência da assinatura (RN-A01 a RN-A04).

São funções puras: não tocam no banco, então rodam em milissegundos e cobrem
as bordas de data, que é onde esse tipo de regra costuma errar.
"""
from datetime import date, timedelta

import pytest

from app.modules.assinatura.regras import (
    DIAS_DE_TESTE,
    DIAS_POR_PAGAMENTO,
    Vigencia,
    inicio_do_teste,
    renovar,
    situacao,
)

HOJE = date(2026, 9, 13)


class TestInicioDoTeste:
    """RN-A01 — conta nova nasce com 7 dias de teste."""

    def test_vale_por_sete_dias(self):
        v = inicio_do_teste(HOJE)
        assert v.valido_ate == HOJE + timedelta(days=DIAS_DE_TESTE)
        assert v.origem == "teste"

    def test_dias_de_teste_sao_sete(self):
        assert DIAS_DE_TESTE == 7


class TestSituacao:
    """O status é derivado das datas, nunca gravado."""

    def test_sem_assinatura_esta_vencida(self):
        assert situacao(None, HOJE) == "vencida"

    def test_dentro_do_teste(self):
        v = Vigencia(valido_ate=HOJE + timedelta(days=3), origem="teste")
        assert situacao(v, HOJE) == "em_teste"

    def test_pago_e_dentro_do_prazo(self):
        v = Vigencia(valido_ate=HOJE + timedelta(days=20), origem="pago")
        assert situacao(v, HOJE) == "ativa"

    def test_ultimo_dia_ainda_vale(self):
        """Vencer "hoje" significa que hoje ainda é válido."""
        v = Vigencia(valido_ate=HOJE, origem="pago")
        assert situacao(v, HOJE) == "ativa"

    def test_dia_seguinte_ao_vencimento_ja_venceu(self):
        v = Vigencia(valido_ate=HOJE - timedelta(days=1), origem="pago")
        assert situacao(v, HOJE) == "vencida"

    def test_teste_expirado_tambem_vence(self):
        v = Vigencia(valido_ate=HOJE - timedelta(days=1), origem="teste")
        assert situacao(v, HOJE) == "vencida"


class TestRenovar:
    """RN-A02 — aprovar soma 30 dias a max(hoje, valido_ate)."""

    def test_renovar_sem_assinatura_conta_de_hoje(self):
        nova = renovar(None, HOJE)
        assert nova.valido_ate == HOJE + timedelta(days=DIAS_POR_PAGAMENTO)
        assert nova.origem == "pago"

    def test_renovar_vencida_conta_de_hoje(self):
        """Quem deixou vencer há 40 dias não ganha os 40 dias de volta."""
        v = Vigencia(valido_ate=HOJE - timedelta(days=40), origem="pago")
        nova = renovar(v, HOJE)
        assert nova.valido_ate == HOJE + timedelta(days=DIAS_POR_PAGAMENTO)

    def test_renovar_adiantado_soma_ao_que_ja_tinha(self):
        """Quem paga faltando 10 dias fica com 10 + 30, não perde os 10."""
        v = Vigencia(valido_ate=HOJE + timedelta(days=10), origem="pago")
        nova = renovar(v, HOJE)
        assert nova.valido_ate == HOJE + timedelta(days=10 + DIAS_POR_PAGAMENTO)

    def test_renovar_durante_o_teste_aproveita_os_dias_restantes(self):
        v = Vigencia(valido_ate=HOJE + timedelta(days=4), origem="teste")
        nova = renovar(v, HOJE)
        assert nova.valido_ate == HOJE + timedelta(days=4 + DIAS_POR_PAGAMENTO)
        assert nova.origem == "pago"

    def test_renovar_no_ultimo_dia_nao_perde_o_dia(self):
        v = Vigencia(valido_ate=HOJE, origem="teste")
        nova = renovar(v, HOJE)
        assert nova.valido_ate == HOJE + timedelta(days=DIAS_POR_PAGAMENTO)

    def test_duas_renovacoes_seguidas_acumulam(self):
        primeira = renovar(None, HOJE)
        segunda = renovar(primeira, HOJE)
        assert segunda.valido_ate == HOJE + timedelta(days=2 * DIAS_POR_PAGAMENTO)

    def test_dias_por_pagamento_sao_trinta(self):
        assert DIAS_POR_PAGAMENTO == 30


class TestPodeEscrever:
    """A pergunta que a trava faz."""

    @pytest.mark.parametrize("origem", ["teste", "pago"])
    def test_dentro_do_prazo_pode(self, origem):
        v = Vigencia(valido_ate=HOJE, origem=origem)
        assert situacao(v, HOJE) in ("ativa", "em_teste")

    def test_vencida_nao_pode(self):
        v = Vigencia(valido_ate=HOJE - timedelta(days=1), origem="pago")
        assert situacao(v, HOJE) == "vencida"
