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

ROTULO_OPCAO = {
    "1_ja_paguei": "Já paguei",
    "2_pago_hoje": "Vou pagar hoje",
    "3_nao_consigo": "Não consigo pagar",
}


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
    def montar_resumo(self, vendedor_id: uuid.UUID, dia: date) -> str | None:
        """Consolida os eventos do dia. Retorna None se não houve atividade
        (RN: dia sem atividade não gera envio)."""
        inicio, fim = datetime.combine(dia, time.min), datetime.combine(dia, time.max)
        logs = [
            log for log, _nome in self.log_repo.listar(vendedor_id, desde=dia)
            if log.tipo != "resumo" and inicio <= log.criado_em <= fim
        ]
        respostas = self.resposta_repo.do_dia(vendedor_id, dia)
        pagamentos = self.parcela_repo.pagas_no_dia(vendedor_id, dia)

        if not logs and not respostas and not pagamentos:
            return None

        enviadas = [l for l in logs if l.status == "enviado"]
        falhas = [l for l in logs if l.status != "enviado"]
        total_recebido = sum(float(p.valor) for p in pagamentos)

        contagem = {chave: 0 for chave in ROTULO_OPCAO}
        for r in respostas:
            contagem[r.opcao] = contagem.get(r.opcao, 0) + 1

        clientes_com_resposta = {r.cliente_id for r in respostas}
        sem_resposta = len({l.cliente_id for l in enviadas} - clientes_com_resposta)

        linhas = [
            f"*Resumo do dia {dia.strftime('%d/%m/%Y')}*",
            "",
            f"📤 Cobranças enviadas: {len(enviadas)}",
            f"✅ Pagamentos confirmados: {len(pagamentos)}",
            f"💰 Valor recebido: {formatar_dinheiro(total_recebido)}",
            "",
            "*Respostas recebidas*",
        ]
        for chave, rotulo in ROTULO_OPCAO.items():
            linhas.append(f"• {rotulo}: {contagem.get(chave, 0)}")
        linhas.append("")
        linhas.append(f"🔕 Clientes sem resposta: {sem_resposta}")
        if falhas:
            linhas.append(f"⚠️ Mensagens não entregues: {len(falhas)}")
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
