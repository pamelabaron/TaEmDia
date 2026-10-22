"""Endpoints de cobranças, conexão do WhatsApp e recebimento de respostas."""
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.agente.service import AgenteService
from app.modules.assinatura.deps import exigir_assinatura_ativa
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.cobrancas.repository import (
    CobrancaLogRepository,
    CobrancaParcelaRepository,
    RespostaRepository,
)
from app.modules.cobrancas.schemas import (
    CobrancaLogOut,
    MensagemRecebida,
    ResultadoRespostaOut,
    StatusWhatsAppOut,
)
from app.modules.cobrancas.service import (
    CobrancaService,
    ParcelaNaoEncontradaError,
)
from app.modules.templates.repository import TemplateRepository
from app.modules.whatsapp.client import get_whatsapp_client
from app.modules.whatsapp.webhook_auth import validar_token_webhook

router = APIRouter(tags=["cobrancas"])


def get_cobranca_service(db: Session = Depends(get_db)) -> CobrancaService:
    return CobrancaService(
        CobrancaLogRepository(db),
        CobrancaParcelaRepository(db),
        TemplateRepository(db),
        get_whatsapp_client(),
    )


def get_agente_service(db: Session = Depends(get_db)) -> AgenteService:
    return AgenteService(
        CobrancaParcelaRepository(db),
        RespostaRepository(db),
        CobrancaLogRepository(db),
        get_whatsapp_client(),
    )


@router.get("/cobrancas", response_model=list[CobrancaLogOut])
def listar_cobrancas(
    periodo: str = "mes",  # hoje | semana | mes
    service: CobrancaService = Depends(get_cobranca_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    """Log das mensagens enviadas, filtrado por período (RF: filtro de cobranças)."""
    hoje = date.today()
    inicio = {
        "hoje": hoje,
        "semana": hoje - timedelta(days=7),
        "mes": hoje - timedelta(days=30),
    }.get(periodo)
    return service.listar_log(vendedor_id, desde=inicio)


@router.post("/cobrancas/{parcela_id}/disparar", response_model=CobrancaLogOut)
def disparar_cobranca(
    parcela_id: uuid.UUID,
    service: CobrancaService = Depends(get_cobranca_service),
    vendedor_id: uuid.UUID = Depends(exigir_assinatura_ativa),
):
    """Disparo manual de cobrança pelo vendedor ('Cobrar agora')."""
    try:
        log = service.disparar_manual(vendedor_id, parcela_id)
    except ParcelaNaoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela não encontrada.")
    if log.status != "enviado":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível enviar agora. A mensagem ficou na fila e será reenviada.",
        )
    return CobrancaLogOut(
        id=log.id, cliente_id=log.cliente_id, cliente_nome="",
        parcela_id=log.parcela_id, tipo=log.tipo, conteudo=log.conteudo,
        status=log.status, criado_em=log.criado_em,
    )


@router.get("/whatsapp/status", response_model=StatusWhatsAppOut)
def status_whatsapp(vendedor_id: uuid.UUID = Depends(exigir_assinatura_ativa)):
    """Estado da conexão com o WhatsApp; traz o QR Code quando desconectado."""
    cliente = get_whatsapp_client()
    s = cliente.status()
    return StatusWhatsAppOut(
        conectado=s.conectado, numero=s.numero, qrcode=s.qrcode, detalhe=s.detalhe,
        modo_simulador=not bool(settings.EVOLUTION_API_KEY),
    )


@router.post("/whatsapp/desconectar", status_code=status.HTTP_204_NO_CONTENT)
def desconectar_whatsapp(vendedor_id: uuid.UUID = Depends(exigir_assinatura_ativa)):
    get_whatsapp_client().desconectar()


@router.post("/whatsapp/webhook", response_model=ResultadoRespostaOut,
             dependencies=[Depends(validar_token_webhook)])
def webhook_whatsapp(
    mensagem: MensagemRecebida,
    agente: AgenteService = Depends(get_agente_service),
):
    """Recebe as mensagens dos devedores (chamado pela Evolution API).

    Não exige JWT: quem chama é o serviço de WhatsApp, não o navegador. O
    remetente é identificado pelo número de telefone.
    """
    resultado = agente.processar_resposta(mensagem.numero, mensagem.texto)
    return ResultadoRespostaOut(
        processada=resultado.processada, motivo=resultado.motivo, opcao=resultado.opcao
    )
