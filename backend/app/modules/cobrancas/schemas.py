"""Formatos de dados das cobranças."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class CobrancaLogOut(BaseModel):
    id: uuid.UUID
    cliente_id: uuid.UUID | None
    cliente_nome: str
    parcela_id: uuid.UUID | None
    tipo: str
    conteudo: str
    status: str
    criado_em: datetime


class StatusWhatsAppOut(BaseModel):
    conectado: bool
    numero: str | None = None
    qrcode: str | None = None
    detalhe: str = ""
    modo_simulador: bool = False


class MensagemRecebida(BaseModel):
    """Entrada do webhook: mensagem recebida de um devedor."""
    numero: str
    texto: str


class ResultadoRespostaOut(BaseModel):
    processada: bool
    motivo: str
    opcao: str | None = None
