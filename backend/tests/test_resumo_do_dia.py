"""Regras do resumo do dia (RN-R01 e RN-R02).

O resumo já existia, mas só como texto pronto para o WhatsApp. Para aparecer na
tela e virar PDF, o cálculo foi separado da formatação: aqui ficam os números,
como função pura, e cada saída (WhatsApp, tela, PDF) escreve do seu jeito.
"""
from collections import namedtuple
from datetime import date, timedelta

import pytest

from app.modules.relatorios.resumo import (
    DIAS_DA_JANELA,
    consolidar,
    dentro_da_janela,
)

HOJE = date(2026, 9, 24)

Log = namedtuple("Log", "status cliente_id tipo")
Resposta = namedtuple("Resposta", "opcao cliente_id")
Parcela = namedtuple("Parcela", "valor")


class TestJanelaDeSeteDias:
    """RN-R01: só os últimos 7 dias podem ser consultados."""

    def test_hoje_vale(self):
        assert dentro_da_janela(HOJE, HOJE)

    def test_seis_dias_atras_vale(self):
        assert dentro_da_janela(HOJE - timedelta(days=6), HOJE)

    def test_sete_dias_atras_ja_saiu(self):
        """Sete dias contando hoje significa hoje e mais seis para trás."""
        assert not dentro_da_janela(HOJE - timedelta(days=7), HOJE)

    def test_amanha_nao_vale(self):
        assert not dentro_da_janela(HOJE + timedelta(days=1), HOJE)

    def test_a_janela_sao_sete_dias(self):
        assert DIAS_DA_JANELA == 7


class TestConsolidacao:
    def test_dia_sem_nada_nao_teve_atividade(self):
        r = consolidar(HOJE, [], [], [])
        assert r.houve_atividade is False
        assert r.cobrancas_enviadas == 0
        assert r.valor_recebido == 0

    def test_conta_enviadas_e_falhas_separadamente(self):
        logs = [
            Log("enviado", "c1", "atraso"),
            Log("enviado", "c2", "lembrete"),
            Log("pendente", "c3", "atraso"),
        ]
        r = consolidar(HOJE, logs, [], [])
        assert r.cobrancas_enviadas == 2
        assert r.cobrancas_falharam == 1
        assert r.houve_atividade is True

    def test_soma_o_valor_recebido(self):
        r = consolidar(HOJE, [], [], [Parcela(100.50), Parcela(49.50)])
        assert r.pagamentos == 2
        assert r.valor_recebido == 150.0

    def test_agrupa_as_respostas_por_opcao(self):
        respostas = [
            Resposta("1_ja_paguei", "c1"),
            Resposta("1_ja_paguei", "c2"),
            Resposta("3_nao_consigo", "c3"),
        ]
        r = consolidar(HOJE, [], respostas, [])
        assert r.respostas["1_ja_paguei"] == 2
        assert r.respostas["3_nao_consigo"] == 1
        assert r.respostas["2_pago_hoje"] == 0

    def test_sem_resposta_conta_clientes_que_receberam_e_nao_responderam(self):
        logs = [Log("enviado", "c1", "atraso"), Log("enviado", "c2", "atraso")]
        respostas = [Resposta("1_ja_paguei", "c1")]
        r = consolidar(HOJE, logs, respostas, [])
        assert r.sem_resposta == 1

    def test_o_mesmo_cliente_cobrado_duas_vezes_conta_uma_no_sem_resposta(self):
        """Duas mensagens para a mesma pessoa não são duas pessoas caladas."""
        logs = [Log("enviado", "c1", "lembrete"), Log("enviado", "c1", "atraso")]
        r = consolidar(HOJE, logs, [], [])
        assert r.cobrancas_enviadas == 2
        assert r.sem_resposta == 1

    def test_falha_de_envio_nao_entra_no_sem_resposta(self):
        """Quem nunca recebeu a mensagem não está deixando de responder."""
        logs = [Log("pendente", "c9", "atraso")]
        r = consolidar(HOJE, logs, [], [])
        assert r.sem_resposta == 0


class TestNumeroQueRecebeOResumo:
    """RN-R03: o resumo pode ir para um número diferente do que cobra.

    Quem cobra é o número do agente. Quem acompanha o negócio pode ser outra
    pessoa, ou a mesma pessoa em outro aparelho.
    """

    def test_usa_o_numero_configurado_quando_existe(self):
        from app.modules.relatorios.resumo import numero_do_resumo
        assert numero_do_resumo("5547999990000", "5547911110000") == "5547999990000"

    def test_cai_no_numero_do_agente_quando_nao_configurado(self):
        from app.modules.relatorios.resumo import numero_do_resumo
        assert numero_do_resumo(None, "5547911110000") == "5547911110000"

    def test_campo_em_branco_conta_como_nao_configurado(self):
        """Campo apagado na tela chega como texto vazio, não como nulo."""
        from app.modules.relatorios.resumo import numero_do_resumo
        assert numero_do_resumo("   ", "5547911110000") == "5547911110000"

    def test_sem_nenhum_dos_dois_nao_ha_para_onde_enviar(self):
        from app.modules.relatorios.resumo import numero_do_resumo
        assert numero_do_resumo(None, None) is None
        assert numero_do_resumo("", "") is None
