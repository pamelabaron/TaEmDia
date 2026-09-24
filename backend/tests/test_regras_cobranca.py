"""Testes das regras do motor de cobrança (RN10, RN11 e escolha de template)."""
from datetime import date, datetime, timedelta

import pytest

from app.modules.cobrancas.regras import (
    MAX_MENSAGENS_DIA,
    OPCOES_RESPOSTA,
    acrescentar_opcoes,
    dentro_horario_comercial,
    escolher_tipo,
    formatar_dinheiro,
    interpretar_resposta,
    montar_contexto,
)

HOJE = date(2026, 8, 25)


class TestHorarioComercial:
    """RN11: envio automático apenas entre 08h e 20h."""

    @pytest.mark.parametrize("hora", [8, 9, 12, 17, 19, 20])
    def test_dentro_do_horario(self, hora):
        assert dentro_horario_comercial(datetime(2026, 8, 25, hora, 0)) is True

    @pytest.mark.parametrize("hora", [0, 5, 7, 21, 23])
    def test_fora_do_horario(self, hora):
        assert dentro_horario_comercial(datetime(2026, 8, 25, hora, 0)) is False

    def test_limite_inferior_exato(self):
        assert dentro_horario_comercial(datetime(2026, 8, 25, 8, 0)) is True
        assert dentro_horario_comercial(datetime(2026, 8, 25, 7, 59)) is False

    def test_limite_superior_exato(self):
        assert dentro_horario_comercial(datetime(2026, 8, 25, 20, 0)) is True
        assert dentro_horario_comercial(datetime(2026, 8, 25, 20, 1)) is False


class TestEscolhaDoTemplate:
    def test_parcela_vencida_usa_template_de_atraso(self):
        assert escolher_tipo(HOJE - timedelta(days=1), HOJE, 3) == "atraso"

    def test_parcela_que_vence_hoje(self):
        assert escolher_tipo(HOJE, HOJE, 3) == "vencimento"

    def test_dentro_da_antecedencia_usa_lembrete(self):
        assert escolher_tipo(HOJE + timedelta(days=3), HOJE, 3) == "lembrete"
        assert escolher_tipo(HOJE + timedelta(days=1), HOJE, 3) == "lembrete"

    def test_fora_da_antecedencia_nao_cobra(self):
        assert escolher_tipo(HOJE + timedelta(days=4), HOJE, 3) is None

    def test_antecedencia_zero_so_cobra_no_vencimento(self):
        assert escolher_tipo(HOJE + timedelta(days=1), HOJE, 0) is None
        assert escolher_tipo(HOJE, HOJE, 0) == "vencimento"


class TestVariaveisDaMensagem:
    def test_contexto_de_parcela_em_atraso(self):
        ctx = montar_contexto("Maria", 150.5, HOJE - timedelta(days=10), HOJE)
        assert ctx["nome_cliente"] == "Maria"
        assert ctx["valor_parcela"] == "R$ 150,50"
        assert ctx["data_vencimento"] == "15/08/2026"
        assert ctx["dias_atraso"] == "10"

    def test_parcela_futura_nao_tem_dias_de_atraso_negativos(self):
        ctx = montar_contexto("João", 100, HOJE + timedelta(days=5), HOJE)
        assert ctx["dias_atraso"] == "0"

    @pytest.mark.parametrize(
        "valor,esperado",
        [(0, "R$ 0,00"), (1, "R$ 1,00"), (99.9, "R$ 99,90"), (1234.56, "R$ 1234,56")],
    )
    def test_formatacao_de_dinheiro(self, valor, esperado):
        assert formatar_dinheiro(valor) == esperado


class TestOpcoesDeResposta:
    def test_acrescenta_opcoes_quando_habilitado(self):
        texto = acrescentar_opcoes("Olá!", habilitado=True)
        assert texto.startswith("Olá!")
        assert "1 - Já paguei" in texto
        assert "2 - Vou pagar hoje" in texto
        assert "3 - Não consigo pagar" in texto

    def test_nao_acrescenta_quando_desabilitado(self):
        assert acrescentar_opcoes("Olá!", habilitado=False) == "Olá!"
        assert OPCOES_RESPOSTA not in acrescentar_opcoes("Olá!", habilitado=False)


class TestInterpretacaoDaResposta:
    @pytest.mark.parametrize(
        "texto,esperado",
        [("1", "1_ja_paguei"), ("2", "2_pago_hoje"), ("3", "3_nao_consigo"),
         (" 1 ", "1_ja_paguei"), ("\n2\n", "2_pago_hoje")],
    )
    def test_opcoes_validas(self, texto, esperado):
        assert interpretar_resposta(texto) == esperado

    @pytest.mark.parametrize("texto", ["oi", "já paguei", "4", "0", "", "   ", "1 já paguei"])
    def test_texto_livre_e_ignorado(self, texto):
        assert interpretar_resposta(texto) is None

    def test_texto_nulo_nao_quebra(self):
        assert interpretar_resposta(None) is None


def test_limite_diario_definido_conforme_o_rfc():
    """RN10: no máximo 3 mensagens automáticas por cliente por dia."""
    assert MAX_MENSAGENS_DIA == 3
