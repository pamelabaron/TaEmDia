"""O dia do sistema é o dia de Brasília, e o resumo sai uma vez por dia.

Dois apontamentos da revisão de código da N1 (PR #1, colega Dereck):

1. O "hoje" vinha de date.today(), que é a data do relógio do container.
   No Docker o relógio é UTC: das 21h à meia-noite de Brasília o container já
   está no dia seguinte. Um disparo manual às 22h tratava a parcela que vence
   amanhã como "vence hoje", e o atraso saía com um dia a mais (RN11 usa
   Brasília; a data também precisa usar).

2. O resumo diário só olhava o relógio: "a hora bate e o minuto está a até 7
   de distância". Se a rodada das 10h00 atrasar e rodar às 10h09, e a das
   10h15 rodar no horário, quem marcou 10h08 recebe dois resumos. Quem garante
   "um por dia" agora é o registro do envio, não o relógio.

Os registros de envio são gravados em UTC (criado_em). Por isso a janela do
dia de Brasília é convertida para UTC antes de consultar o banco.
"""
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from app.modules.cobrancas.regras import (
    dia_em_brasilia,
    hoje_brasilia,
    janela_utc_do_dia,
)

BRASILIA = ZoneInfo("America/Sao_Paulo")


# ------------------------------------------------------------ regras puras
class TestHojeEmBrasilia:
    def test_as_22h_de_brasilia_ainda_e_o_mesmo_dia(self):
        # 22h de 06/11 em Brasília = 01h de 07/11 em UTC.
        agora_utc = datetime(2026, 11, 7, 1, 0, tzinfo=ZoneInfo("UTC"))
        assert hoje_brasilia(agora_utc) == date(2026, 11, 6)

    def test_de_manha_o_dia_e_o_mesmo_nos_dois_relogios(self):
        agora_utc = datetime(2026, 11, 7, 12, 0, tzinfo=ZoneInfo("UTC"))
        assert hoje_brasilia(agora_utc) == date(2026, 11, 7)

    def test_sem_argumento_usa_o_relogio_de_brasilia(self):
        assert hoje_brasilia() == datetime.now(BRASILIA).date()


class TestJanelaDoDia:
    def test_o_dia_de_brasilia_comeca_as_3h_utc(self):
        inicio, fim = janela_utc_do_dia(date(2026, 11, 6))
        assert inicio == datetime(2026, 11, 6, 3, 0)
        assert fim == datetime(2026, 11, 7, 3, 0)

    def test_a_janela_e_ingenua_como_o_criado_em(self):
        # criado_em é gravado sem fuso (datetime.utcnow); comparar com um
        # valor com fuso daria erro no banco.
        inicio, fim = janela_utc_do_dia(date(2026, 11, 6))
        assert inicio.tzinfo is None and fim.tzinfo is None


class TestDiaDeUmRegistro:
    def test_registro_da_1h_utc_pertence_ao_dia_anterior_em_brasilia(self):
        assert dia_em_brasilia(datetime(2026, 11, 7, 1, 0)) == date(2026, 11, 6)

    def test_registro_do_meio_dia_utc_e_do_mesmo_dia(self):
        assert dia_em_brasilia(datetime(2026, 11, 7, 12, 0)) == date(2026, 11, 7)


# --------------------------------------------------------- guarda no código
def test_cobranca_e_agendador_nao_usam_o_relogio_do_container():
    """Se alguém voltar a escrever date.today() nestes módulos, o bug volta."""
    raiz = Path(__file__).resolve().parents[1] / "app" / "modules"
    arquivos = [
        raiz / "cobrancas" / "service.py",
        raiz / "agente" / "agendador.py",
        raiz / "agente" / "service.py",
    ]
    culpados = [str(a.name) for a in arquivos if "date.today()" in a.read_text(encoding="utf-8")]
    assert culpados == [], f"date.today() usa o dia UTC do container: {culpados}"


# ---------------------------------------------- disparo manual às 22h
def test_disparo_as_22h_trata_a_parcela_de_amanha_como_lembrete(db, vendedor, monkeypatch):
    """22h de Brasília, container já no dia seguinte em UTC. A parcela vence
    amanhã (em Brasília): é lembrete, não "vence hoje"."""
    from app.modules.clientes.models import Cliente
    from app.modules.cobrancas import service as modulo
    from app.modules.cobrancas.repository import CobrancaLogRepository, CobrancaParcelaRepository
    from app.modules.cobrancas.service import CobrancaService
    from app.modules.templates.repository import TemplateRepository
    from app.modules.vendas.models import Parcela, Venda
    from app.modules.whatsapp.client import SimuladorWhatsAppClient

    hoje_br = date(2026, 11, 6)
    amanha_br = date(2026, 11, 7)
    # Relógio do container: 01h de 07/11 UTC.
    momento = datetime(2026, 11, 6, 22, 0, tzinfo=BRASILIA)
    monkeypatch.setattr(modulo, "agora_brasilia", lambda: momento, raising=False)

    class DataDoContainer(date):
        @classmethod
        def today(cls):
            return amanha_br
    monkeypatch.setattr(modulo, "date", DataDoContainer)

    cliente = Cliente(vendedor_id=vendedor.id, nome="Odete", whatsapp_numero="5547999990009")
    db.add(cliente)
    db.commit()
    venda = Venda(vendedor_id=vendedor.id, cliente_id=cliente.id, valor_total=50,
                  num_parcelas=1, data_primeira_parcela=amanha_br)
    db.add(venda)
    db.commit()
    parcela = Parcela(venda_id=venda.id, numero_parcela=1, valor=50, data_vencimento=amanha_br)
    db.add(parcela)
    db.commit()

    escolhidos = []
    original = modulo.escolher_tipo
    monkeypatch.setattr(modulo, "escolher_tipo",
                        lambda venc, hoje, **kw: escolhidos.append(hoje) or original(venc, hoje, **kw))

    servico = CobrancaService(CobrancaLogRepository(db), CobrancaParcelaRepository(db),
                              TemplateRepository(db), SimuladorWhatsAppClient())
    servico.disparar_manual(vendedor.id, parcela.id)

    assert escolhidos == [hoje_br], f"O disparo usou o dia {escolhidos}, e não o de Brasília."


# -------------------------------------------------- resumo uma vez por dia
def _preparar_resumo(db, vendedor, monkeypatch, horario: time):
    from app.modules.agente import agendador
    from app.modules.agente.service import AgenteService
    from app.modules.configuracoes.repository import ConfiguracaoRepository
    from app.modules.whatsapp.client import SimuladorWhatsAppClient

    vendedor.whatsapp_numero = "5547999998888"
    config = ConfiguracaoRepository(db).buscar(vendedor.id) or ConfiguracaoRepository(db).criar(vendedor.id)
    config.horario_resumo = horario
    config.resumo_ativo = True
    db.commit()

    simulador = SimuladorWhatsAppClient()
    monkeypatch.setattr(agendador, "get_whatsapp_client", lambda: simulador)
    monkeypatch.setattr(agendador, "SessionLocal", lambda: _SessaoQueNaoFecha(db))
    # O conteúdo do resumo não importa aqui, só quantas vezes ele sai.
    monkeypatch.setattr(AgenteService, "montar_resumo", lambda self, vid, dia: "Resumo do dia")
    return agendador, simulador


class _SessaoQueNaoFecha:
    """A sessão do teste, sem o close() do agendador (ela é usada depois)."""
    def __init__(self, db):
        self._db = db

    def __getattr__(self, nome):
        return getattr(self._db, nome)

    def close(self):
        pass


def test_rodada_atrasada_e_rodada_no_horario_mandam_um_resumo_so(db, vendedor, monkeypatch):
    """Resumo marcado para 10h08. A rodada das 10h00 atrasa e roda às 10h09;
    a das 10h15 roda no horário. As duas caem na janela de 7 minutos."""
    agendador, simulador = _preparar_resumo(db, vendedor, monkeypatch, time(10, 8))

    # O dia é o de hoje: o registro do envio é gravado com o relógio real.
    hoje = datetime.now(BRASILIA).date()
    for hora, minuto in ((10, 9), (10, 15)):
        momento = datetime.combine(hoje, time(hora, minuto), tzinfo=BRASILIA)
        monkeypatch.setattr(agendador, "agora_brasilia", lambda m=momento: m)
        agendador.job_resumo_diario()

    from app.modules.cobrancas.models import CobrancaLog
    resumos = db.query(CobrancaLog).filter(
        CobrancaLog.vendedor_id == vendedor.id, CobrancaLog.tipo == "resumo"
    ).count()
    assert resumos == 1, f"O vendedor recebeu {resumos} resumos no mesmo dia."
