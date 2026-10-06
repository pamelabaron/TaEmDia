"""Regras puras do motor de cobrança (sem banco e sem HTTP). Fáceis de testar."""
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

# RN11: envio automático apenas em horário comercial.
HORA_INICIO = time(8, 0)
HORA_FIM = time(20, 0)

# RN10: no máximo 3 mensagens automáticas por cliente por dia.
MAX_MENSAGENS_DIA = 3

OPCOES_RESPOSTA = (
    "\n\nResponda com o número:\n"
    "1 - Já paguei\n"
    "2 - Vou pagar hoje\n"
    "3 - Não consigo pagar"
)


def agora_brasilia() -> datetime:
    return datetime.now(FUSO_BRASILIA)


def dentro_horario_comercial(momento: datetime | None = None) -> bool:
    """RN11: entre 08h00 e 20h00 no horário de Brasília."""
    momento = momento or agora_brasilia()
    return HORA_INICIO <= momento.time() <= HORA_FIM


def escolher_tipo(
    data_vencimento: date, hoje: date, dias_antecedencia: int
) -> str | None:
    """Decide qual template usar, ou None se ainda não é hora de cobrar.

    - 'lembrete'   -> faltam até `dias_antecedencia` dias para vencer
    - 'vencimento' -> vence hoje
    - 'atraso'     -> já venceu
    """
    if data_vencimento < hoje:
        return "atraso"
    if data_vencimento == hoje:
        return "vencimento"
    if (data_vencimento - hoje).days <= dias_antecedencia:
        return "lembrete"
    return None


def formatar_dinheiro(valor) -> str:
    return "R$ " + f"{float(valor):.2f}".replace(".", ",")


def montar_contexto(nome_cliente: str, valor, data_vencimento: date, hoje: date) -> dict:
    """Valores das variáveis dinâmicas dos templates."""
    dias_atraso = max((hoje - data_vencimento).days, 0)
    return {
        "nome_cliente": nome_cliente,
        "valor_parcela": formatar_dinheiro(valor),
        "data_vencimento": data_vencimento.strftime("%d/%m/%Y"),
        "dias_atraso": str(dias_atraso),
    }


def acrescentar_opcoes(texto: str, habilitado: bool) -> str:
    """Acrescenta as opções numeradas de resposta ao final da mensagem (RF30)."""
    return texto + OPCOES_RESPOSTA if habilitado else texto


def interpretar_resposta(texto: str) -> str | None:
    """Traduz a resposta do devedor para a opção correspondente.

    Aceita apenas as opções numeradas; texto livre é ignorado (RN: canal
    unidirecional). Retorna None quando a mensagem não é uma opção válida.
    """
    limpo = (texto or "").strip()
    mapa = {"1": "1_ja_paguei", "2": "2_pago_hoje", "3": "3_nao_consigo"}
    return mapa.get(limpo)


RESPOSTA_CANAL_FECHADO = (
    "Este canal é destinado apenas ao recebimento de cobranças. "
    "Para mais informações, entre em contato diretamente com o vendedor."
)
