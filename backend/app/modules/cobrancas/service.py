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
        # Uma cobrança por parcela por dia, contando a manual e a que está na
        # fila. A varredura roda de hora em hora e, sem isto, repetia a mesma
        # cobrança até o limite de 3 por dia.
        ja_cobradas = self.log_repo.parcelas_cobradas_no_dia(vendedor_id, hoje)

        for parcela, _venda, cliente in self.parcela_repo.elegiveis(vendedor_id, hoje, limite_data):
            if parcela.id in ja_cobradas:
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
    def reenviar_pendentes(self, vendedor_id: uuid.UUID, hoje: date | None = None) -> int:
        """Reenvia as mensagens que ficaram na fila após queda de conexão (FE01).

        Chamado pela tarefa horária do agendador, antes da varredura. Esta
        função existia desde o começo e ninguém a chamava: a mensagem que
        falhava ficava na fila para sempre.

        Antes de reenviar, confere se a cobrança ainda faz sentido. Enquanto
        a mensagem esperava, o mundo pode ter mudado, e cada caso abaixo é
        **descartado**, não enviado:

        - a mensagem é de outro dia: o texto envelheceu ("atrasada há 10 dias"
          virou 11), e a varredura de hoje manda uma versão atualizada;
        - a parcela foi paga, ou o cliente respondeu que pagou (RN12);
        - a venda foi cancelada, ou o cliente foi desativado;
        - era automática e o envio automático do cliente foi desligado.

        Vai sempre para o número **atual** do cliente, e respeita o limite
        diário (RN10): o reenvio também é uma mensagem automática.

        Devolve quantas mensagens saíram.
        """
        hoje = hoje or date.today()
        reenviadas = 0
        contagem: dict[uuid.UUID, int] = {}

        for log, cliente, parcela, venda in self.log_repo.pendentes_de_reenvio(vendedor_id):
            motivo = self._motivo_para_descartar(log, cliente, parcela, venda, hoje)
            if motivo:
                log.status = "descartada"
                log.detalhe = motivo
                continue

            if cliente.id not in contagem:
                contagem[cliente.id] = self.log_repo.contar_do_dia(vendedor_id, cliente.id, hoje)
            if log.tipo != "manual" and contagem[cliente.id] >= MAX_MENSAGENS_DIA:
                continue  # RN10: fica na fila, e expira amanhã

            resultado = self.whatsapp.enviar_mensagem(cliente.whatsapp_numero, log.conteudo)
            if resultado.sucesso:
                log.status = "enviado"
                log.enviado_em = datetime.utcnow()
                log.detalhe = resultado.detalhe or None
                contagem[cliente.id] += 1
                reenviadas += 1

        self.log_repo.salvar()
        return reenviadas

    @staticmethod
    def _motivo_para_descartar(log, cliente, parcela, venda, hoje: date) -> str | None:
        """Por que esta mensagem da fila não deve mais sair. None se deve."""
        if log.criado_em.date() != hoje:
            return "Expirou na fila. A varredura do dia manda uma cobrança atualizada."
        if cliente is None or not cliente.ativo:
            return "O cliente foi desativado enquanto a mensagem esperava."
        if parcela is None:
            return None
        if parcela.data_pagamento is not None:
            return "A parcela foi paga enquanto a mensagem esperava."
        if parcela.aguardando_confirmacao:
            return "O cliente respondeu que já pagou enquanto a mensagem esperava."
        if venda is not None and venda.status != "ativa":
            return "A venda foi cancelada enquanto a mensagem esperava."
        if log.tipo != "manual" and not cliente.envio_auto_ativo:
            return "O envio automático deste cliente foi desligado."
        return None

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
