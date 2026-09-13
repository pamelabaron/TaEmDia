"""Regras de vigência da assinatura (RN-A01 a RN-A03).

Funções puras: recebem datas, devolvem datas. Nenhuma toca no banco, o que
mantém a suíte rápida e permite cobrir as bordas de data com facilidade.

A situação da assinatura é **derivada**, nunca gravada — mesma convenção do
status da parcela. Gravar status significa mantê-lo sincronizado com a
passagem do tempo, e é assim que um sistema passa a mentir.
"""
from dataclasses import dataclass
from datetime import date, timedelta

#: Dias de cortesia para quem acabou de criar a conta (RN-A01).
DIAS_DE_TESTE = 7

#: Dias somados a cada comprovante aprovado (RN-A02).
DIAS_POR_PAGAMENTO = 30

#: Situações em que o vendedor pode gravar.
SITUACOES_COM_ACESSO = ("ativa", "em_teste")


@dataclass(frozen=True)
class Vigencia:
    """Até quando o acesso de escrita vale, e de onde esse prazo veio."""

    valido_ate: date
    origem: str  # "teste" ou "pago"


def inicio_do_teste(hoje: date) -> Vigencia:
    """Vigência de uma conta recém-criada (RN-A01)."""
    return Vigencia(valido_ate=hoje + timedelta(days=DIAS_DE_TESTE), origem="teste")


def situacao(vigencia: Vigencia | None, hoje: date) -> str:
    """Situação atual: ``em_teste``, ``ativa`` ou ``vencida``.

    Quem nunca teve assinatura conta como vencida — é o estado mais restritivo,
    e portanto o seguro para se errar.
    """
    if vigencia is None:
        return "vencida"
    if hoje > vigencia.valido_ate:
        return "vencida"
    return "em_teste" if vigencia.origem == "teste" else "ativa"


def renovar(vigencia: Vigencia | None, hoje: date) -> Vigencia:
    """Aplica um pagamento aprovado (RN-A02).

    Os 30 dias somam a partir do que for maior entre hoje e a validade atual.
    Assim quem paga adiantado não perde os dias que ainda tinha, e quem deixou
    vencer não recupera o período parado.
    """
    base = hoje
    if vigencia is not None and vigencia.valido_ate > hoje:
        base = vigencia.valido_ate
    return Vigencia(valido_ate=base + timedelta(days=DIAS_POR_PAGAMENTO), origem="pago")


def pode_escrever(vigencia: Vigencia | None, hoje: date) -> bool:
    """Pergunta que a trava dos endpoints de escrita faz."""
    return situacao(vigencia, hoje) in SITUACOES_COM_ACESSO
