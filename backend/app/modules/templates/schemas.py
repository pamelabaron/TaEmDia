"""Formatos de dados dos templates de mensagem."""
import uuid

from pydantic import BaseModel, ConfigDict


class TemplateUpdate(BaseModel):
    """Campos editáveis de um template."""
    titulo: str | None = None
    corpo: str | None = None
    ativo: bool | None = None


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: str
    titulo: str
    corpo: str
    is_padrao: bool
    ativo: bool


class PreviewIn(BaseModel):
    """Texto a ser pré-visualizado com dados de exemplo."""
    corpo: str


class PreviewOut(BaseModel):
    resultado: str
