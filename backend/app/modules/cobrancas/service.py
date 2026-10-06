"""Serviço de cobrança: seleciona o template, aplica as variáveis, envia pelo
WhatsApp Client e registra o histórico. Respeita as regras de negócio do RFC."""
import uuid
from datetime import date, datetime, timedelta

from app.modules.clientes.models import Cliente
from app.modules.cobrancas.models import CobrancaLog
from app.modules.cobrancas.regras import (
    MAX_MENSAGENS_DIA,
    acrescentar_opcoes,
    dentro_horario_comercial,
    escolher_tipo,
    montar_contexto,
)
from app.modules.cobrancas.repository import (
    CobrancaLogRepository,
    CobrancaParcelaRepository,
)
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.service import TemplateService, renderizar
from app.modules.vendas.models import Parcela
from app.modules.whatsapp.client import WhatsAppClient


class ParcelaNaoEncontradaError(Exception):
    pass


class LimiteDiarioAtingidoError(Exception):
    """RN10: já foram enviadas 3 mensagens hoje para este cliente."""


class CobrancaService:
    def __init__(
        self,
        log_repo: CobrancaLogRepository,
        parcela_repo: CobrancaParcelaRepository,
        template_repo: TemplateRepository,
        whatsapp: WhatsAppClient,
    ):
        self.log_repo = log_repo
        self.parcela_repo = parcela_repo
        self.template_repo = template_repo
        self.templates = TemplateService(template_repo)
        self.whatsapp = whatsapp

    # ------------------------------------------------------------------ envio
    def _texto_da_cobranca(
        self, vendedor_id: uuid.UUID, cliente: Cliente, parcela: Parcela, tipo: str, hoje: date
    ) -> str:
        self.templates.listar(vendedor_id)  # garante os templates padrão criados
        template = self.template_repo.buscar_por_tipo(vendedor_id, tipo)
        corpo = template.corpo if template else "Olá {nome_cliente}, sua parcela de {valor_parcela} venceu em {data_vencimento}."
        contexto = montar_contexto(cliente.nome, parcela.valor, parcela.data_vencimento, hoje)
        return acrescentar_opcoes(renderizar(corpo, contexto), cliente.interacao_habilitada)

    def _enviar_e_registrar(
        self,
        vendedor_id: uuid.UUID,
        cliente: Cliente,
        parcela: Parcela | None,
        tipo: str,
        texto: str,
    ) -> CobrancaLog:
        resultado = self.whatsapp.enviar_mensagem(cliente.whatsapp_numero, texto)
        log = CobrancaLog(
            vendedor_id=vendedor_id,
            cliente_id=cliente.id,
            parcela_id=parcela.id if parcela is not None else None,
            tipo=tipo,
            conteudo=texto,
            # Falha de conexão deixa a mensagem na fila para reenvio (FE01).
            status="enviado" if resultado.sucesso else "pendente",
            detalhe=resultado.detalhe or None,
            enviado_em=datetime.utcnow() if resultado.sucesso else None,
        )
        return self.log_repo.registrar(log)

    def disparar_manual(self, vendedor_id: uuid.UUID, parcela_id: uuid.UUID) -> CobrancaLog:
        """Disparo manual pelo vendedor (RF: cobrar agora).

        O disparo manual é uma decisão explícita do vendedor: não depende do
        horário comercial nem do envio automático do cliente.
        """
        encontrado = self.parcela_repo.por_id(vendedor_id, parcela_id)
        if encontrado is None:
            raise ParcelaNaoEncontradaError()
        parcela, _venda, cliente = encontrado
        hoje = date.today()
        tipo = escolher_tipo(parcela.data_vencimento, hoje, dias_antecedencia=999) or "atraso"
        texto = self._texto_da_cobranca(vendedor_id, cliente, parcela, tipo, hoje)
        return self._enviar_e_registrar(vendedor_id, cliente, parcela, "manual", texto)

    # ------------------------------------------------- varredura automática
    def varrer_e_cobrar(
        self, vendedor_id: uuid.UUID, dias_antecedencia: int, hoje: date | None = None,
        ignorar_horario: bool = False,
    ) -> list[CobrancaLog]:
        """Percorre as parcelas elegíveis e envia as cobranças automáticas.

        Respeita: horário comercial (RN11), limite diário por cliente (RN10) e o
        sinalizador de envio automático de cada cliente.
        """
        hoje = hoje or date.today()
        if not ignorar_horario and not dentro_horario_comercial():
            return []

        limite_data = hoje + timedelta(days=max(dias_antecedencia, 0))
        enviados: list[CobrancaLog] = []
        contagem_cache: dict[uuid.UUID, int] = {}

        for parcela, venda, cliente in self.parcela_repo.elegiveis(hoje, limite_data):
            if venda.vendedor_id != vendedor_id:
                continue
            tipo = escolher_tipo(parcela.data_vencimento, hoje, dias_antecedencia)
            if tipo is None:
                continue

            if cliente.id not in contagem_cache:
                contagem_cache[cliente.id] = self.log_repo.contar_do_dia(vendedor_id, cliente.id, hoje)
            if contagem_cache[cliente.id] >= MAX_MENSAGENS_DIA:
                continue  # RN10

            texto = self._texto_da_cobranca(vendedor_id, cliente, parcela, tipo, hoje)
            log = self._enviar_e_registrar(vendedor_id, cliente, parcela, tipo, texto)
            if log.status == "enviado":
                contagem_cache[cliente.id] += 1
            enviados.append(log)

        return enviados

    # --------------------------------------------------------- fila de reenvio
    def reenviar_pendentes(self, numeros_por_cliente: dict[uuid.UUID, str]) -> int:
        """Reenvia as mensagens que ficaram na fila após queda de conexão (FE01)."""
        reenviadas = 0
        for log in self.log_repo.pendentes_de_reenvio():
            numero = numeros_por_cliente.get(log.cliente_id)
            if not numero:
                continue
            resultado = self.whatsapp.enviar_mensagem(numero, log.conteudo)
            if resultado.sucesso:
                log.status = "enviado"
                log.enviado_em = datetime.utcnow()
                log.detalhe = resultado.detalhe or None
                reenviadas += 1
        self.log_repo.salvar()
        return reenviadas

    # ------------------------------------------------------------------ log
    def listar_log(self, vendedor_id: uuid.UUID, desde: date | None = None) -> list[dict]:
        return [
            {
                "id": log.id,
                "cliente_id": log.cliente_id,
                "cliente_nome": nome,
                "parcela_id": log.parcela_id,
                "tipo": log.tipo,
                "conteudo": log.conteudo,
                "status": log.status,
                "criado_em": log.criado_em,
            }
            for log, nome in self.log_repo.listar(vendedor_id, desde)
        ]
