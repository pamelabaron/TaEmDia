"""Schemas Pydantic: definem o formato dos dados que entram e saem da API."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClienteCreate(BaseModel):
    """Dados para cadastrar um cliente (RF04)."""
    nome: str
    whatsapp_numero: str
    cpf: str | None = None
    endereco: str | None = None


class ClienteUpdate(BaseModel):
    """Campos editáveis de um cliente (RF06). Todos opcionais."""
    nome: str | None = None
    cpf: str | None = None
    endereco: str | None = None
    envio_auto_ativo: bool | None = None
    interacao_habilitada: bool | None = None


class ClienteOut(BaseModel):
    """Formato de saída de um cliente."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    whatsapp_numero: str
    cpf: str | None
    endereco: str | None
    envio_auto_ativo: bool
    interacao_habilitada: bool
    ativo: bool
    criado_em: datetime
