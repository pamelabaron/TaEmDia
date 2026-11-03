"""Uma cobrança por parcela por dia, e nenhuma para quem disse que já pagou.

A varredura automática roda de hora em hora, das 8h às 20h (agendador.py).
O que impede o mesmo cliente de receber a mesma cobrança às 8h05, 9h05 e
10h05? Até aqui, só o limite de 3 mensagens por dia (RN10). Mas o limite é um
teto, não uma meta: um cliente com uma parcela atrasada recebia as três.

O teste antigo de limite diário (test_api_cobrancas.py) não pegava isso por
acaso: o cenário dele tem três parcelas, a primeira varredura gasta as três
mensagens, e a segunda não tem o que mandar. Ele prova o teto, e não prova a
repetição. Aqui o cenário tem **uma** parcela, que é o caso comum.

E o caso mais delicado: quem responde "1 - Já paguei" tem a parcela marcada
como aguardando conferência (RN12). Continuar cobrando essa pessoa é
exatamente o constrangimento que os Termos de Uso dizem para não fazer.
"""
from datetime import date, timedelta

import pytest

from app.modules.cobrancas.repository import CobrancaLogRepository, CobrancaParcelaRepository
from app.modules.cobrancas.service import CobrancaService
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
def uma_atrasada(db, vendedor):
    """Cliente com uma única parcela, atrasada há 10 dias."""
    from app.modules.clientes.models import Cliente
    from app.modules.vendas.models import Parcela, Venda

    cliente = Cliente(vendedor_id=vendedor.id, nome="Rosangela", whatsapp_numero="5547999990001")
    db.add(cliente)
    db.commit()
    venda = Venda(vendedor_id=vendedor.id, cliente_id=cliente.id, valor_total=100,
                  num_parcelas=1, data_primeira_parcela=HOJE - timedelta(days=10))
    db.add(venda)
    db.commit()
    parcela = Parcela(venda_id=venda.id, numero_parcela=1, valor=100,
                      data_vencimento=HOJE - timedelta(days=10))
    db.add(parcela)
    db.commit()
    db.refresh(parcela)
    return {"cliente": cliente, "venda": venda, "parcela": parcela}


def _varrer(servico, vendedor):
    return servico.varrer_e_cobrar(vendedor.id, dias_antecedencia=3, ignorar_horario=True)


class TestUmaCobrancaPorParcelaPorDia:
    def test_a_segunda_varredura_do_dia_nao_repete(self, servico, uma_atrasada, vendedor, whatsapp):
        primeira = _varrer(servico, vendedor)
        segunda = _varrer(servico, vendedor)

        assert len(primeira) == 1
        assert segunda == [], (
            "A mesma parcela foi cobrada de novo na varredura seguinte. Como "
            "ela roda de hora em hora, o cliente receberia a mesma cobrança "
            "até bater o limite de 3 por dia."
        )
        assert len(whatsapp.enviadas) == 1

    def test_o_dia_inteiro_de_varreduras_manda_uma_so(self, servico, uma_atrasada, vendedor, whatsapp):
        """As 13 rodadas do agendador, das 8h às 20h."""
        for _ in range(13):
            _varrer(servico, vendedor)
        assert len(whatsapp.enviadas) == 1

    def test_cobranca_manual_do_dia_conta(self, servico, uma_atrasada, vendedor, whatsapp):
        """Se a vendedora já cobrou na mão hoje, o automático não repete."""
        servico.disparar_manual(vendedor.id, uma_atrasada["parcela"].id)
        assert _varrer(servico, vendedor) == []
        assert len(whatsapp.enviadas) == 1

    def test_no_dia_seguinte_cobra_de_novo(self, servico, uma_atrasada, vendedor, whatsapp):
        """Não é para parar de cobrar: é uma por dia."""
        servico.varrer_e_cobrar(vendedor.id, 3, hoje=HOJE, ignorar_horario=True)
        amanha = servico.varrer_e_cobrar(vendedor.id, 3, hoje=HOJE + timedelta(days=1),
                                         ignorar_horario=True)
        assert len(amanha) == 1


class TestQuemDisseQuePagou:
    def test_parcela_aguardando_conferencia_nao_e_cobrada(self, servico, uma_atrasada, db, vendedor):
        uma_atrasada["parcela"].aguardando_confirmacao = True
        db.commit()
        assert _varrer(servico, vendedor) == [], (
            "O cliente respondeu que já pagou e continuou sendo cobrado. A "
            "parcela espera a conferência da vendedora, não outra cobrança."
        )

    def test_o_disparo_manual_continua_possivel(self, servico, uma_atrasada, db, vendedor):
        """A vendedora conferiu, não achou o pagamento, e decide cobrar.
        É decisão dela: o manual não é bloqueado."""
        uma_atrasada["parcela"].aguardando_confirmacao = True
        db.commit()
        log = servico.disparar_manual(vendedor.id, uma_atrasada["parcela"].id)
        assert log.status == "enviado"


# ------------------------------------------------------------------ reenvio
class WhatsAppInstavel:
    """Simula a conexão caindo e voltando."""

    def __init__(self):
        self.no_ar = False
        self.enviadas: list[tuple[str, str]] = []

    def enviar_mensagem(self, numero, texto):
        from app.modules.whatsapp.client import ResultadoEnvio
        if not self.no_ar:
            return ResultadoEnvio(sucesso=False, detalhe="sem conexão")
        self.enviadas.append((numero, texto))
        return ResultadoEnvio(sucesso=True, detalhe="ok")


@pytest.fixture()
def instavel():
    return WhatsAppInstavel()


@pytest.fixture()
def servico_instavel(db, instavel):
    return CobrancaService(
        CobrancaLogRepository(db), CobrancaParcelaRepository(db),
        TemplateRepository(db), instavel,
    )


def _logs(db, parcela):
    from app.modules.cobrancas.models import CobrancaLog
    return db.query(CobrancaLog).filter(CobrancaLog.parcela_id == parcela.id).all()


class TestReenvioQuandoAConexaoVolta:
    """FE01: a mensagem que falhou fica na fila e sai quando a conexão volta."""

    def test_falha_deixa_na_fila(self, servico_instavel, uma_atrasada, vendedor, db):
        _varrer(servico_instavel, vendedor)
        assert [l.status for l in _logs(db, uma_atrasada["parcela"])] == ["pendente"]

    def test_a_conexao_volta_e_a_mensagem_sai(self, servico_instavel, instavel, uma_atrasada, vendedor, db):
        _varrer(servico_instavel, vendedor)
        instavel.no_ar = True

        assert servico_instavel.reenviar_pendentes(vendedor.id) == 1
        assert [l.status for l in _logs(db, uma_atrasada["parcela"])] == ["enviado"]
        assert instavel.enviadas[0][0] == "5547999990001"

    def test_fora_do_ar_a_fila_nao_enche_de_copias(self, servico_instavel, uma_atrasada, vendedor, db):
        """Com o WhatsApp caído o dia todo, cada rodada criava outra mensagem."""
        for _ in range(13):
            _varrer(servico_instavel, vendedor)
        assert len(_logs(db, uma_atrasada["parcela"])) == 1

    def test_reenvio_e_depois_varredura_mandam_uma_so(self, servico_instavel, instavel, uma_atrasada, vendedor):
        """A ordem do agendador: primeiro a fila, depois a varredura."""
        _varrer(servico_instavel, vendedor)
        instavel.no_ar = True
        servico_instavel.reenviar_pendentes(vendedor.id)
        _varrer(servico_instavel, vendedor)
        assert len(instavel.enviadas) == 1

    def test_vai_para_o_numero_atual_do_cliente(self, servico_instavel, instavel, uma_atrasada, vendedor, db):
        """Se o número mudou enquanto a mensagem esperava, vale o novo."""
        _varrer(servico_instavel, vendedor)
        uma_atrasada["cliente"].whatsapp_numero = "5547988887777"
        db.commit()
        instavel.no_ar = True
        servico_instavel.reenviar_pendentes(vendedor.id)
        assert instavel.enviadas[0][0] == "5547988887777"


class TestReenvioQueNaoFazMaisSentido:
    """Enquanto a mensagem esperava, o mundo mudou. Ela é descartada, não enviada."""

    def _descartada(self, db, parcela):
        logs = _logs(db, parcela)
        return len(logs) == 1 and logs[0].status == "descartada"

    def test_parcela_paga_enquanto_esperava(self, servico_instavel, instavel, uma_atrasada, vendedor, db):
        _varrer(servico_instavel, vendedor)
        uma_atrasada["parcela"].data_pagamento = HOJE
        db.commit()
        instavel.no_ar = True

        assert servico_instavel.reenviar_pendentes(vendedor.id) == 0
        assert instavel.enviadas == [], "Cobrou uma parcela que já estava paga."
        assert self._descartada(db, uma_atrasada["parcela"])

    def test_cliente_disse_que_pagou_enquanto_esperava(self, servico_instavel, instavel, uma_atrasada, vendedor, db):
        _varrer(servico_instavel, vendedor)
        uma_atrasada["parcela"].aguardando_confirmacao = True
        db.commit()
        instavel.no_ar = True
        servico_instavel.reenviar_pendentes(vendedor.id)
        assert instavel.enviadas == []
        assert self._descartada(db, uma_atrasada["parcela"])

    def test_venda_cancelada_enquanto_esperava(self, servico_instavel, instavel, uma_atrasada, vendedor, db):
        _varrer(servico_instavel, vendedor)
        uma_atrasada["venda"].status = "cancelada"
        db.commit()
        instavel.no_ar = True
        servico_instavel.reenviar_pendentes(vendedor.id)
        assert instavel.enviadas == []
        assert self._descartada(db, uma_atrasada["parcela"])

    def test_envio_automatico_desligado_para_o_cliente(self, servico_instavel, instavel, uma_atrasada, vendedor, db):
        _varrer(servico_instavel, vendedor)
        uma_atrasada["cliente"].envio_auto_ativo = False
        db.commit()
        instavel.no_ar = True
        servico_instavel.reenviar_pendentes(vendedor.id)
        assert instavel.enviadas == []
        assert self._descartada(db, uma_atrasada["parcela"])

    def test_mensagem_de_ontem_expira(self, servico_instavel, instavel, uma_atrasada, vendedor, db):
        """O texto de ontem está velho ("atrasada há 10 dias" virou 11). A
        varredura de hoje manda uma cobrança atualizada no lugar."""
        _varrer(servico_instavel, vendedor)
        log = _logs(db, uma_atrasada["parcela"])[0]
        log.criado_em = log.criado_em - timedelta(days=1)
        db.commit()
        instavel.no_ar = True

        servico_instavel.reenviar_pendentes(vendedor.id)
        assert instavel.enviadas == []
        assert log.status == "descartada"

        _varrer(servico_instavel, vendedor)
        assert len(instavel.enviadas) == 1, "A cobrança atualizada de hoje não saiu."


class TestReenvioRespeitaAsRegras:
    def test_so_mexe_na_fila_da_propria_conta(self, servico_instavel, instavel, uma_atrasada, vendedor, db):
        from app.modules.vendedores.models import Vendedor

        _varrer(servico_instavel, vendedor)
        outra = Vendedor(google_email="outra@teste.local", nome="Outra")
        db.add(outra)
        db.commit()
        instavel.no_ar = True

        assert servico_instavel.reenviar_pendentes(outra.id) == 0
        assert [l.status for l in _logs(db, uma_atrasada["parcela"])] == ["pendente"]

    def test_respeita_o_limite_diario(self, servico_instavel, instavel, uma_atrasada, vendedor, db):
        """RN10 vale para o reenvio também: ele é uma mensagem automática."""
        from app.modules.cobrancas.models import CobrancaLog

        _varrer(servico_instavel, vendedor)
        for _ in range(3):
            db.add(CobrancaLog(vendedor_id=vendedor.id, cliente_id=uma_atrasada["cliente"].id,
                               tipo="atraso", conteudo="x", status="enviado"))
        db.commit()
        instavel.no_ar = True

        assert servico_instavel.reenviar_pendentes(vendedor.id) == 0
        assert instavel.enviadas == []


class TestOAgendadorChamaOReenvio:
    """A função existia desde o começo e ninguém a chamava. Este é o teste
    que teria pego isso: ele roda a tarefa do agendador e confere a chamada."""

    def test_a_varredura_horaria_reenvia_antes_de_cobrar(self, uma_atrasada, vendedor, monkeypatch):
        from app.modules.agente import agendador

        ordem = []
        monkeypatch.setattr(agendador, "dentro_horario_comercial", lambda: True)
        monkeypatch.setattr(agendador, "get_whatsapp_client", lambda: SimuladorWhatsAppClient())
        monkeypatch.setattr(CobrancaService, "reenviar_pendentes",
                            lambda self, vid, hoje=None: ordem.append(("reenvio", vid)) or 0)
        monkeypatch.setattr(CobrancaService, "varrer_e_cobrar",
                            lambda self, vid, dias, **kw: ordem.append(("varredura", vid)) or [])

        agendador.job_varredura_cobrancas()

        assert ("reenvio", vendedor.id) in ordem, "A tarefa horária não chama o reenvio (FE01)."
        assert ordem.index(("reenvio", vendedor.id)) < ordem.index(("varredura", vendedor.id)), (
            "O reenvio precisa vir antes: senão a varredura vê a parcela como "
            "já cobrada (a mensagem está na fila) e a fila nunca anda na mesma rodada."
        )
