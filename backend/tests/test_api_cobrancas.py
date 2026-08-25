"""Testes do motor de cobrança e das respostas dos devedores."""
import uuid
from datetime import date, timedelta

import pytest

from app.modules.cobrancas.repository import (
    CobrancaLogRepository,
    CobrancaParcelaRepository,
    RespostaRepository,
)
from app.modules.cobrancas.service import CobrancaService, ParcelaNaoEncontradaError
from app.modules.templates.repository import TemplateRepository
from app.modules.whatsapp.client import SimuladorWhatsAppClient

HOJE = date.today()


@pytest.fixture()
def whatsapp():
    return SimuladorWhatsAppClient()


@pytest.fixture()
def servico(db, whatsapp):
    return CobrancaService(
        CobrancaLogRepository(db), CobrancaParcelaRepository(db),
        TemplateRepository(db), whatsapp,
    )


@pytest.fixture()
def cenario(db, vendedor):
    """Cliente com 3 parcelas: uma atrasada, uma vencendo hoje e uma futura."""
    from app.modules.clientes.models import Cliente
    from app.modules.vendas.models import Parcela, Venda

    cliente = Cliente(vendedor_id=vendedor.id, nome="Rosangela", whatsapp_numero="5547999990001")
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    venda = Venda(vendedor_id=vendedor.id, cliente_id=cliente.id, valor_total=300,
                  num_parcelas=3, data_primeira_parcela=HOJE - timedelta(days=40))
    db.add(venda)
    db.commit()
    db.refresh(venda)

    datas = [HOJE - timedelta(days=40), HOJE, HOJE + timedelta(days=2)]
    for i, d in enumerate(datas, start=1):
        db.add(Parcela(venda_id=venda.id, numero_parcela=i, valor=100, data_vencimento=d))
    db.commit()

    parcelas = db.query(Parcela).filter(Parcela.venda_id == venda.id).order_by(
        Parcela.numero_parcela).all()
    return {"vendedor": vendedor, "cliente": cliente, "venda": venda, "parcelas": parcelas}


class TestDisparoManual:
    def test_envia_e_registra_no_historico(self, servico, cenario, whatsapp, vendedor):
        log = servico.disparar_manual(vendedor.id, cenario["parcelas"][0].id)
        assert log.status == "enviado"
        assert log.tipo == "manual"
        assert len(whatsapp.enviadas) == 1

    def test_mensagem_leva_os_dados_do_cliente(self, servico, cenario, whatsapp, vendedor):
        servico.disparar_manual(vendedor.id, cenario["parcelas"][0].id)
        _numero, texto = whatsapp.enviadas[0]
        assert "Rosangela" in texto
        assert "R$ 100,00" in texto
        assert "{" not in texto  # todas as variáveis foram substituídas

    def test_mensagem_vai_para_o_numero_do_cliente(self, servico, cenario, whatsapp, vendedor):
        servico.disparar_manual(vendedor.id, cenario["parcelas"][0].id)
        numero, _texto = whatsapp.enviadas[0]
        assert numero == "5547999990001"

    def test_inclui_opcoes_de_resposta(self, servico, cenario, whatsapp, vendedor):
        servico.disparar_manual(vendedor.id, cenario["parcelas"][0].id)
        _numero, texto = whatsapp.enviadas[0]
        assert "1 - Já paguei" in texto

    def test_parcela_inexistente(self, servico, vendedor):
        with pytest.raises(ParcelaNaoEncontradaError):
            servico.disparar_manual(vendedor.id, uuid.uuid4())

    def test_nao_dispara_parcela_de_outro_vendedor(self, servico, cenario, db):
        from app.modules.vendedores.models import Vendedor

        outro = Vendedor(google_email="outro@x.com", nome="Outro")
        db.add(outro)
        db.commit()
        db.refresh(outro)
        with pytest.raises(ParcelaNaoEncontradaError):
            servico.disparar_manual(outro.id, cenario["parcelas"][0].id)


class TestVarreduraAutomatica:
    def test_cobra_atrasada_e_vencendo_hoje(self, servico, cenario, vendedor):
        enviados = servico.varrer_e_cobrar(vendedor.id, dias_antecedencia=0, ignorar_horario=True)
        assert sorted(e.tipo for e in enviados) == ["atraso", "vencimento"]

    def test_antecedencia_inclui_o_lembrete(self, servico, cenario, vendedor):
        enviados = servico.varrer_e_cobrar(vendedor.id, dias_antecedencia=3, ignorar_horario=True)
        assert "lembrete" in [e.tipo for e in enviados]

    def test_respeita_limite_diario(self, servico, cenario, vendedor):
        """RN10: no máximo 3 mensagens automáticas por cliente por dia."""
        servico.varrer_e_cobrar(vendedor.id, dias_antecedencia=3, ignorar_horario=True)
        segunda = servico.varrer_e_cobrar(vendedor.id, dias_antecedencia=3, ignorar_horario=True)
        assert segunda == []

    def test_nao_cobra_cliente_com_envio_desligado(self, servico, cenario, db, vendedor):
        cenario["cliente"].envio_auto_ativo = False
        db.commit()
        assert servico.varrer_e_cobrar(vendedor.id, dias_antecedencia=3, ignorar_horario=True) == []

    def test_nao_cobra_parcela_ja_paga(self, servico, cenario, db, vendedor):
        for p in cenario["parcelas"]:
            p.data_pagamento = HOJE
        db.commit()
        assert servico.varrer_e_cobrar(vendedor.id, dias_antecedencia=3, ignorar_horario=True) == []

    def test_nao_cobra_venda_cancelada(self, servico, cenario, db, vendedor):
        cenario["venda"].status = "cancelada"
        db.commit()
        assert servico.varrer_e_cobrar(vendedor.id, dias_antecedencia=3, ignorar_horario=True) == []

    def test_nao_cobra_de_outro_vendedor(self, servico, cenario, db):
        from app.modules.vendedores.models import Vendedor

        outro = Vendedor(google_email="outro2@x.com", nome="Outro 2")
        db.add(outro)
        db.commit()
        db.refresh(outro)
        assert servico.varrer_e_cobrar(outro.id, dias_antecedencia=3, ignorar_horario=True) == []


class TestHistorico:
    def test_log_traz_o_nome_do_cliente(self, servico, cenario, vendedor):
        servico.disparar_manual(vendedor.id, cenario["parcelas"][0].id)
        log = servico.listar_log(vendedor.id)
        assert len(log) == 1
        assert log[0]["cliente_nome"] == "Rosangela"

    def test_log_vazio_quando_nao_houve_envio(self, servico, vendedor):
        assert servico.listar_log(vendedor.id) == []


class TestApiCobrancas:
    def test_listar_exige_autenticacao(self, cliente_http):
        assert cliente_http.get("/cobrancas").status_code == 401

    def test_disparar_exige_autenticacao(self, cliente_http):
        assert cliente_http.post(f"/cobrancas/{uuid.uuid4()}/disparar").status_code == 401

    def test_status_do_whatsapp(self, cliente_http, cabecalho_auth):
        resp = cliente_http.get("/whatsapp/status", headers=cabecalho_auth)
        assert resp.status_code == 200
        assert "conectado" in resp.json()

    def test_parcela_inexistente_retorna_404(self, cliente_http, cabecalho_auth):
        resp = cliente_http.post(f"/cobrancas/{uuid.uuid4()}/disparar", headers=cabecalho_auth)
        assert resp.status_code == 404
