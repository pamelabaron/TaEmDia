"""Testes dos cálculos de vendas e parcelas (RN06, RN07, RN09)."""
from datetime import date
from decimal import Decimal

import pytest

from app.modules.vendas.models import Parcela
from app.modules.vendas.service import _dividir_valor, _somar_meses, calcular_status


class TestDivisaoEmParcelas:
    def test_divisao_exata(self):
        valores = _dividir_valor(300.0, 3)
        assert valores == [Decimal("100.00")] * 3

    def test_soma_fecha_com_o_total_mesmo_com_dizima(self):
        """100 / 3 não é exato: os centavos que sobram vão para as últimas parcelas."""
        valores = _dividir_valor(100.0, 3)
        assert sum(valores) == Decimal("100.00")
        assert valores == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]

    def test_a_vista_gera_uma_parcela_com_o_total(self):
        assert _dividir_valor(1500.0, 1) == [Decimal("1500.00")]

    @pytest.mark.parametrize("total,n", [(0.03, 2), (10.01, 3), (999.99, 7), (1.0, 1), (50.0, 60)])
    def test_soma_sempre_fecha(self, total, n):
        valores = _dividir_valor(total, n)
        assert len(valores) == n
        assert sum(valores) == Decimal(str(round(total, 2)))

    def test_centavos_ficam_nas_ultimas_parcelas(self):
        valores = _dividir_valor(10.0, 3)
        assert valores[0] <= valores[-1]


class TestVencimentosMensais:
    def test_soma_simples_de_meses(self):
        assert _somar_meses(date(2026, 1, 10), 1) == date(2026, 2, 10)
        assert _somar_meses(date(2026, 1, 10), 3) == date(2026, 4, 10)

    def test_virada_de_ano(self):
        assert _somar_meses(date(2026, 11, 15), 2) == date(2027, 1, 15)
        assert _somar_meses(date(2026, 12, 1), 12) == date(2027, 12, 1)

    def test_dia_31_ajusta_para_o_ultimo_dia_do_mes(self):
        """31/01 + 1 mês = 28/02 (não existe 31 de fevereiro)."""
        assert _somar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)
        assert _somar_meses(date(2026, 1, 31), 3) == date(2026, 4, 30)

    def test_fevereiro_em_ano_bissexto(self):
        assert _somar_meses(date(2028, 1, 31), 1) == date(2028, 2, 29)

    def test_zero_meses_mantem_a_data(self):
        assert _somar_meses(date(2026, 5, 20), 0) == date(2026, 5, 20)

    def test_parcelamento_longo_de_60_meses(self):
        assert _somar_meses(date(2026, 1, 15), 59) == date(2030, 12, 15)


class TestStatusDaParcela:
    """RN09: o status é derivado da data e das ações do vendedor."""

    HOJE = date(2026, 8, 25)

    def _parcela(self, vencimento, pagamento=None, aguardando=False):
        p = Parcela(numero_parcela=1, valor=Decimal("100.00"),
                    data_vencimento=vencimento, data_pagamento=pagamento)
        p.aguardando_confirmacao = aguardando
        return p

    def test_futura_e_pendente(self):
        assert calcular_status(self._parcela(date(2026, 9, 10)), self.HOJE) == "pendente"

    def test_vence_hoje_ainda_e_pendente(self):
        assert calcular_status(self._parcela(self.HOJE), self.HOJE) == "pendente"

    def test_vencida_sem_pagamento_e_atrasada(self):
        assert calcular_status(self._parcela(date(2026, 8, 24)), self.HOJE) == "atrasada"

    def test_com_pagamento_e_paga(self):
        p = self._parcela(date(2026, 8, 1), pagamento=date(2026, 8, 20))
        assert calcular_status(p, self.HOJE) == "paga"

    def test_paga_tem_prioridade_sobre_aguardando(self):
        p = self._parcela(date(2026, 8, 1), pagamento=date(2026, 8, 20), aguardando=True)
        assert calcular_status(p, self.HOJE) == "paga"

    def test_resposta_ja_paguei_deixa_aguardando_confirmacao(self):
        """A opção 1 do devedor NÃO dá baixa: só o vendedor confirma."""
        p = self._parcela(date(2026, 8, 1), aguardando=True)
        assert calcular_status(p, self.HOJE) == "aguardando_confirmacao"
