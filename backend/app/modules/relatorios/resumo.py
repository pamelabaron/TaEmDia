"""Consolidação do resumo do dia (RN-R01 e RN-R02).

Funções puras: recebem listas, devolvem números. Nenhuma toca no banco nem
escreve texto. Isso permite que as três saídas do resumo (a mensagem do
WhatsApp, a tela e o PDF) usem o mesmo cálculo, em vez de cada uma repetir a
conta e discordarem com o tempo.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable

#: Quantos dias para trás a consulta alcança, contando hoje (RN-R01).
DIAS_DA_JANELA = 7

#: Respostas possíveis do devedor, com o rótulo que aparece para o vendedor.
#: As chaves são as mesmas gravadas no banco pelo agente.
ROTULO_OPCAO = {
    "1_ja_paguei": "Já paguei",
    "2_pago_hoje": "Vou pagar hoje",
    "3_nao_consigo": "Não consigo pagar",
}
OPCOES = tuple(ROTULO_OPCAO)


@dataclass(frozen=True)
class ResumoDoDia:
    dia: date
    cobrancas_enviadas: int
    cobrancas_falharam: int
    pagamentos: int
    valor_recebido: float
    respostas: dict[str, int] = field(default_factory=dict)
    sem_resposta: int = 0

    @property
    def houve_atividade(self) -> bool:
        """Dia parado não vira mensagem nem preenche a tela (RN-R02)."""
        return bool(
            self.cobrancas_enviadas
            or self.cobrancas_falharam
            or self.pagamentos
            or sum(self.respostas.values())
        )


def dentro_da_janela(dia: date, hoje: date) -> bool:
    """O dia pode ser consultado? (RN-R01)

    Sete dias contando hoje significa hoje e mais seis para trás. Datas futuras
    ficam de fora: não há o que resumir de um dia que não aconteceu.
    """
    primeiro = hoje - timedelta(days=DIAS_DA_JANELA - 1)
    return primeiro <= dia <= hoje


def dias_da_janela(hoje: date) -> list[date]:
    """Os dias consultáveis, do mais recente para o mais antigo."""
    return [hoje - timedelta(days=n) for n in range(DIAS_DA_JANELA)]


def consolidar(
    dia: date, logs: Iterable, respostas: Iterable, pagamentos: Iterable
) -> ResumoDoDia:
    """Transforma os eventos do dia nos números do resumo.

    `sem_resposta` conta **pessoas**, não mensagens: cobrar alguém duas vezes no
    mesmo dia não faz dois silêncios. E quem não chegou a receber a mensagem não
    entra na conta, porque não está deixando de responder.
    """
    logs = list(logs)
    respostas = list(respostas)
    pagamentos = list(pagamentos)

    enviadas = [l for l in logs if l.status == "enviado"]
    falharam = [l for l in logs if l.status != "enviado"]

    contagem = {opcao: 0 for opcao in OPCOES}
    for r in respostas:
        contagem[r.opcao] = contagem.get(r.opcao, 0) + 1

    responderam = {r.cliente_id for r in respostas}
    receberam = {l.cliente_id for l in enviadas}

    return ResumoDoDia(
        dia=dia,
        cobrancas_enviadas=len(enviadas),
        cobrancas_falharam=len(falharam),
        pagamentos=len(pagamentos),
        valor_recebido=round(sum(float(p.valor) for p in pagamentos), 2),
        respostas=contagem,
        sem_resposta=len(receberam - responderam),
    )


def numero_do_resumo(configurado: str | None, do_agente: str | None) -> str | None:
    """Para qual WhatsApp o resumo vai (RN-R03).

    Quem cobra é o número do agente. Quem acompanha o negócio pode ser outro:
    um sócio, o contador, ou a mesma pessoa em outro aparelho. Sem número
    próprio configurado, o resumo segue para o do agente.

    Campo apagado na tela chega como texto vazio, não como nulo, por isso a
    checagem olha o conteúdo e não só a ausência.
    """
    escolhido = (configurado or "").strip()
    if escolhido:
        return escolhido
    reserva = (do_agente or "").strip()
    return reserva or None
