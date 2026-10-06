"""Agente de cobrança: processa as respostas dos devedores e gera o resumo diário
(RFC 5.3.5)."""
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time

from app.modules.cobrancas.models import CobrancaLog, RespostaDevedor
from app.modules.cobrancas.regras import (
    RESPOSTA_CANAL_FECHADO,
    formatar_dinheiro,
    interpretar_resposta,
)
from app.modules.cobrancas.repository import (
    CobrancaLogRepository,
    CobrancaParcelaRepository,
    RespostaRepository,
)
from app.modules.whatsapp.client import WhatsAppClient

# Rótulos e cálculo moram juntos, para tela, PDF e WhatsApp
# usarem os mesmos nomes e os mesmos números.
from app.modules.relatorios.resumo import (  # noqa: E402
    ROTULO_OPCAO,
    ResumoDoDia,
    consolidar,
)


@dataclass
class ResultadoResposta:
    processada: bool
    motivo: str
    opcao: str | None = None


class AgenteService:
    def __init__(
        self,
        parcela_repo: CobrancaParcelaRepository,
        resposta_repo: RespostaRepository,
        log_repo: CobrancaLogRepository,
        whatsapp: WhatsAppClient,
    ):
        self.parcela_repo = parcela_repo
        self.resposta_repo = resposta_repo
        self.log_repo = log_repo
        self.whatsapp = whatsapp

    # ------------------------------------------------- respostas do devedor
    def processar_resposta(self, numero: str, texto: str) -> ResultadoResposta:
        """Processa uma mensagem recebida de um devedor (UC09)."""
        encontrado = self.parcela_repo.aberta_mais_antiga_por_numero(numero)
        if encontrado is None:
            return ResultadoResposta(False, "numero_sem_parcela_aberta")
        parcela, venda, cliente = encontrado

        opcao = interpretar_resposta(texto)
        if opcao is None:
            # Texto livre é ignorado; o agente responde que o canal é só de cobrança.
            self.whatsapp.enviar_mensagem(numero, RESPOSTA_CANAL_FECHADO)
            return ResultadoResposta(False, "texto_livre_ignorado")

        # RN12/FE04: a mesma opção só é processada uma vez por parcela.
        if self.resposta_repo.ja_registrada(parcela.id, opcao):
            return ResultadoResposta(False, "resposta_duplicada", opcao)

        self.resposta_repo.registrar(
            RespostaDevedor(
                vendedor_id=venda.vendedor_id,
                cliente_id=cliente.id,
                parcela_id=parcela.id,
                opcao=opcao,
            )
        )

        # Opção 1 NÃO confirma o pagamento: apenas sinaliza para o vendedor conferir.
        if opcao == "1_ja_paguei":
            parcela.aguardando_confirmacao = True
            self.parcela_repo.salvar()

        return ResultadoResposta(True, "registrada", opcao)

    # ----------------------------------------------------- resumo analítico
    def dados_do_resumo(self, vendedor_id: uuid.UUID, dia: date) -> ResumoDoDia:
        """Busca os eventos do dia e devolve os números já consolidados.

        Quem escreve o texto é quem consome: a mensagem do WhatsApp, a tela e o
        PDF partem daqui, então não há como um dizer um número e outro dizer
        outro.
        """
        inicio, fim = datetime.combine(dia, time.min), datetime.combine(dia, time.max)
        logs = [
            log for log, _nome in self.log_repo.listar(vendedor_id, desde=dia)
            if log.tipo != "resumo" and inicio <= log.criado_em <= fim
        ]
        respostas = self.resposta_repo.do_dia(vendedor_id, dia)
        pagamentos = self.parcela_repo.pagas_no_dia(vendedor_id, dia)
        return consolidar(dia, logs, respostas, pagamentos)

    def montar_resumo(self, vendedor_id: uuid.UUID, dia: date) -> str | None:
        """Texto do resumo para o WhatsApp. Retorna None se o dia não teve
        atividade (RN-R02: dia parado não gera envio)."""
        r = self.dados_do_resumo(vendedor_id, dia)
        if not r.houve_atividade:
            return None

        linhas = [
            f"*Resumo do dia {dia.strftime('%d/%m/%Y')}*",
            "",
            f"📤 Cobranças enviadas: {r.cobrancas_enviadas}",
            f"✅ Pagamentos confirmados: {r.pagamentos}",
            f"💰 Valor recebido: {formatar_dinheiro(r.valor_recebido)}",
            "",
            "*Respostas recebidas*",
        ]
        for chave, rotulo in ROTULO_OPCAO.items():
            linhas.append(f"• {rotulo}: {r.respostas.get(chave, 0)}")
        linhas.append("")
        linhas.append(f"🔕 Clientes sem resposta: {r.sem_resposta}")
        if r.cobrancas_falharam:
            linhas.append(f"⚠️ Mensagens não entregues: {r.cobrancas_falharam}")
        return "\n".join(linhas)


    def enviar_resumo(
        self, vendedor_id: uuid.UUID, numero_vendedor: str, dia: date
    ) -> CobrancaLog | None:
        """Envia o resumo diário ao WhatsApp do vendedor (UC10)."""
        texto = self.montar_resumo(vendedor_id, dia)
        if texto is None or not numero_vendedor:
            return None
        resultado = self.whatsapp.enviar_mensagem(numero_vendedor, texto)
        return self.log_repo.registrar(
            CobrancaLog(
                vendedor_id=vendedor_id,
                cliente_id=None,  # o resumo vai para o vendedor, não para um cliente
                parcela_id=None,
                tipo="resumo",
                conteudo=texto,
                status="enviado" if resultado.sucesso else "pendente",
                detalhe=resultado.detalhe or None,
                enviado_em=datetime.utcnow() if resultado.sucesso else None,
            )
        )
