"""Testes do agente: respostas do devedor (UC09) e resumo diário (UC10)."""
from datetime import date, timedelta

import pytest

from app.modules.agente.service import AgenteService
from app.modules.cobrancas.models import CobrancaLog
from app.modules.cobrancas.repository import (
    CobrancaLogRepository,
    CobrancaParcelaRepository,
    RespostaRepository,
)
from app.modules.whatsapp.client import SimuladorWhatsAppClient

HOJE = date.today()
NUMERO = "5547999990001"


@pytest.fixture()
def whatsapp():
    return SimuladorWhatsAppClient()


@pytest.fixture()
def agente(db, whatsapp):
    return AgenteService(
        CobrancaParcelaRepository(db), RespostaRepository(db),
        CobrancaLogRepository(db), whatsapp,
    )


@pytest.fixture()
def cenario(db, vendedor):
    from app.modules.clientes.models import Cliente
    from app.modules.vendas.models import Parcela, Venda

    cliente = Cliente(vendedor_id=vendedor.id, nome="Rosangela", whatsapp_numero=NUMERO)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    venda = Venda(vendedor_id=vendedor.id, cliente_id=cliente.id, valor_total=200,
                  num_parcelas=2, data_primeira_parcela=HOJE - timedelta(days=30))
    db.add(venda)
    db.commit()
    db.refresh(venda)

    for i, d in enumerate([HOJE - timedelta(days=30), HOJE - timedelta(days=1)], start=1):
        db.add(Parcela(venda_id=venda.id, numero_parcela=i, valor=100, data_vencimento=d))
    db.commit()

    parcelas = db.query(Parcela).filter(Parcela.venda_id == venda.id).order_by(
        Parcela.numero_parcela).all()
    return {"cliente": cliente, "venda": venda, "parcelas": parcelas}


class TestRespostasDoDevedor:
    def test_opcao_1_registra_e_marca_aguardando(self, agente, cenario, db):
        """RN: 'já paguei' NÃO confirma o pagamento — só sinaliza para o vendedor."""
        r = agente.processar_resposta(NUMERO, "1")
        assert r.processada is True
        assert r.opcao == "1_ja_paguei"

        db.refresh(cenario["parcelas"][0])
        assert cenario["parcelas"][0].aguardando_confirmacao is True
        assert cenario["parcelas"][0].data_pagamento is None

    def test_opcao_2_registra_sem_alterar_a_parcela(self, agente, cenario, db):
        r = agente.processar_resposta(NUMERO, "2")
        assert r.opcao == "2_pago_hoje"
        db.refresh(cenario["parcelas"][0])
        assert cenario["parcelas"][0].aguardando_confirmacao is False

    def test_opcao_3_registra_a_negativa(self, agente, cenario):
        assert agente.processar_resposta(NUMERO, "3").opcao == "3_nao_consigo"

    def test_resposta_vai_para_a_parcela_mais_antiga_em_aberto(self, agente, cenario, db):
        """RN14: associa à parcela de vencimento mais antigo."""
        agente.processar_resposta(NUMERO, "1")
        db.refresh(cenario["parcelas"][0])
        db.refresh(cenario["parcelas"][1])
        assert cenario["parcelas"][0].aguardando_confirmacao is True
        assert cenario["parcelas"][1].aguardando_confirmacao is False

    def test_texto_livre_e_ignorado_com_aviso(self, agente, cenario, whatsapp):
        r = agente.processar_resposta(NUMERO, "oi, tudo bem?")
        assert r.processada is False
        assert r.motivo == "texto_livre_ignorado"
        assert len(whatsapp.enviadas) == 1
        assert "apenas ao recebimento de cobranças" in whatsapp.enviadas[0][1]

    def test_resposta_repetida_e_processada_uma_unica_vez(self, agente, cenario):
        """RN12/FE04: a mesma opção só conta uma vez por parcela."""
        assert agente.processar_resposta(NUMERO, "1").processada is True
        segunda = agente.processar_resposta(NUMERO, "1")
        assert segunda.processada is False
        assert segunda.motivo == "resposta_duplicada"

    def test_numero_desconhecido(self, agente, cenario):
        r = agente.processar_resposta("5547000000000", "1")
        assert r.processada is False
        assert r.motivo == "numero_sem_parcela_aberta"

    def test_cliente_sem_parcela_em_aberto(self, agente, cenario, db):
        for p in cenario["parcelas"]:
            p.data_pagamento = HOJE
        db.commit()
        assert agente.processar_resposta(NUMERO, "1").processada is False


class TestResumoDiario:
    def test_dia_sem_atividade_nao_gera_resumo(self, agente, vendedor):
        """RN: dias sem atividade não geram envio."""
        assert agente.montar_resumo(vendedor.id, HOJE) is None

    def test_resumo_conta_as_cobrancas_enviadas(self, agente, cenario, db, vendedor):
        db.add(CobrancaLog(vendedor_id=vendedor.id, cliente_id=cenario["cliente"].id,
                           parcela_id=cenario["parcelas"][0].id, tipo="atraso",
                           conteudo="teste", status="enviado"))
        db.commit()
        texto = agente.montar_resumo(vendedor.id, HOJE)
        assert "Cobranças enviadas: 1" in texto

    def test_resumo_traz_pagamentos_e_valor(self, agente, cenario, db, vendedor):
        cenario["parcelas"][0].data_pagamento = HOJE
        db.commit()
        texto = agente.montar_resumo(vendedor.id, HOJE)
        assert "Pagamentos confirmados: 1" in texto
        assert "R$ 100,00" in texto

    def test_resumo_agrupa_as_respostas_por_tipo(self, agente, cenario, db, vendedor):
        agente.processar_resposta(NUMERO, "1")
        texto = agente.montar_resumo(vendedor.id, HOJE)
        assert "Já paguei: 1" in texto
        assert "Vou pagar hoje: 0" in texto

    def test_envio_do_resumo_registra_no_historico(self, agente, cenario, db, vendedor, whatsapp):
        cenario["parcelas"][0].data_pagamento = HOJE
        db.commit()
        log = agente.enviar_resumo(vendedor.id, vendedor.whatsapp_numero, HOJE)
        assert log is not None
        assert log.tipo == "resumo"
        assert whatsapp.enviadas[-1][0] == vendedor.whatsapp_numero

    def test_nao_envia_resumo_sem_numero_do_vendedor(self, agente, cenario, db, vendedor):
        cenario["parcelas"][0].data_pagamento = HOJE
        db.commit()
        assert agente.enviar_resumo(vendedor.id, "", HOJE) is None

    def test_nao_envia_resumo_em_dia_sem_atividade(self, agente, vendedor):
        assert agente.enviar_resumo(vendedor.id, vendedor.whatsapp_numero, HOJE) is None


class TestWebhook:
    def test_webhook_processa_resposta(self, cliente_http, cenario):
        resp = cliente_http.post("/whatsapp/webhook", json={"numero": NUMERO, "texto": "1"})
        assert resp.status_code == 200
        assert resp.json()["processada"] is True

    def test_webhook_nao_exige_autenticacao(self, cliente_http, cenario):
        """Quem chama é o serviço de WhatsApp, não o navegador."""
        resp = cliente_http.post("/whatsapp/webhook", json={"numero": NUMERO, "texto": "2"})
        assert resp.status_code != 401

    def test_webhook_ignora_texto_livre(self, cliente_http, cenario):
        resp = cliente_http.post("/whatsapp/webhook", json={"numero": NUMERO, "texto": "bom dia"})
        assert resp.json()["processada"] is False
