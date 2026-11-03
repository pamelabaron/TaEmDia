"""Testes da classificação de pagadores (RN15/RN16)."""
from datetime import date, timedelta

import pytest

from app.modules.relatorios.ranking import ParcelaRanking, classificar

HOJE = date(2026, 8, 25)


def paga_em_dia(dias_antes: int = 30) -> ParcelaRanking:
    venc = HOJE - timedelta(days=dias_antes)
    return ParcelaRanking(data_vencimento=venc, data_pagamento=venc)


def paga_com_atraso(dias_atraso: int, dias_antes: int = 30) -> ParcelaRanking:
    venc = HOJE - timedelta(days=dias_antes)
    return ParcelaRanking(data_vencimento=venc, data_pagamento=venc + timedelta(days=dias_atraso))


def aberta_vencida(dias: int) -> ParcelaRanking:
    return ParcelaRanking(data_vencimento=HOJE - timedelta(days=dias), data_pagamento=None)


def aberta_futura(dias: int = 10) -> ParcelaRanking:
    return ParcelaRanking(data_vencimento=HOJE + timedelta(days=dias), data_pagamento=None)


class TestSemHistorico:
    def test_cliente_sem_parcelas(self):
        r = classificar([], HOJE)
        assert r.categoria == "sem_historico"
        assert r.total_avaliadas == 0

    def test_apenas_parcelas_futuras_nao_conta(self):
        """Parcela que ainda não venceu é neutra: não classifica o cliente."""
        r = classificar([aberta_futura(), aberta_futura(20)], HOJE)
        assert r.categoria == "sem_historico"
        assert r.total_avaliadas == 0


class TestBomPagador:
    def test_todas_pagas_em_dia(self):
        r = classificar([paga_em_dia() for _ in range(5)], HOJE)
        assert r.categoria == "bom"
        assert r.percentual_em_dia == 100.0
        assert r.media_dias_atraso == 0.0

    def test_pagamento_antecipado_conta_como_em_dia(self):
        venc = HOJE - timedelta(days=20)
        antecipada = ParcelaRanking(venc, venc - timedelta(days=5))
        r = classificar([antecipada] * 3, HOJE)
        assert r.categoria == "bom"

    def test_um_atraso_pequeno_em_dez_ainda_e_bom(self):
        """90% em dia e média de atraso abaixo de 3 dias."""
        parcelas = [paga_em_dia() for _ in range(9)] + [paga_com_atraso(2)]
        r = classificar(parcelas, HOJE)
        assert r.categoria == "bom"
        assert r.percentual_em_dia == 90.0

    def test_parcelas_futuras_nao_prejudicam(self):
        parcelas = [paga_em_dia() for _ in range(3)] + [aberta_futura()]
        r = classificar(parcelas, HOJE)
        assert r.categoria == "bom"
        assert r.total_avaliadas == 3


class TestInadimplente:
    def test_mais_de_30_por_cento_em_atraso(self):
        """2 de 5 = 40% em atraso."""
        parcelas = [paga_em_dia() for _ in range(3)] + [paga_com_atraso(5), paga_com_atraso(7)]
        r = classificar(parcelas, HOJE)
        assert r.categoria == "inadimplente"

    def test_parcela_em_aberto_ha_mais_de_60_dias(self):
        """Mesmo com o resto em dia, uma parcela muito antiga marca inadimplência."""
        parcelas = [paga_em_dia() for _ in range(20)] + [aberta_vencida(61)]
        r = classificar(parcelas, HOJE)
        assert r.categoria == "inadimplente"

    def test_exatamente_60_dias_ainda_nao_e_inadimplente_por_esse_criterio(self):
        parcelas = [paga_em_dia() for _ in range(20)] + [aberta_vencida(60)]
        r = classificar(parcelas, HOJE)
        assert r.categoria != "inadimplente"

    def test_todas_em_atraso(self):
        r = classificar([aberta_vencida(10), aberta_vencida(20)], HOJE)
        assert r.categoria == "inadimplente"
        assert r.percentual_em_dia == 0.0


class TestPagadorRegular:
    def test_poucos_atrasos_mas_media_alta(self):
        """10% em atraso (não é inadimplente), mas atraso grande derruba de 'bom'."""
        parcelas = [paga_em_dia() for _ in range(9)] + [paga_com_atraso(40)]
        r = classificar(parcelas, HOJE)
        assert r.categoria == "regular"

    def test_um_atraso_em_cinco_e_regular(self):
        """20% em atraso: abaixo de 30% (não inadimplente) e abaixo de 90% em dia."""
        parcelas = [paga_em_dia() for _ in range(4)] + [paga_com_atraso(1)]
        r = classificar(parcelas, HOJE)
        assert r.categoria == "regular"
        assert r.percentual_em_dia == 80.0


class TestMetricas:
    def test_media_de_atraso_e_calculada_sobre_todas_as_avaliadas(self):
        parcelas = [paga_em_dia(), paga_em_dia(), paga_com_atraso(6), paga_com_atraso(6)]
        r = classificar(parcelas, HOJE)
        assert r.media_dias_atraso == 3.0  # (0+0+6+6)/4
        assert r.total_avaliadas == 4

    def test_valores_sao_arredondados(self):
        parcelas = [paga_em_dia(), paga_em_dia(), paga_com_atraso(1)]
        r = classificar(parcelas, HOJE)
        assert r.percentual_em_dia == pytest.approx(66.7, abs=0.1)
