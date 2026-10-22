"""Formatos de dados dos templates de mensagem."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

#: Aparece na listagem de mensagens. Mais que isso não cabe na linha da tela.
TITULO_MAXIMO = 60

#: O WhatsApp aceita bem mais (4096), mas cobrança longa ninguém lê até o fim,
#: e texto gigante é a forma mais barata de pesar o envio de todo mundo.
CORPO_MAXIMO = 1000


class TemplateUpdate(BaseModel):
    """Campos editáveis de um template."""
    titulo: str | None = Field(default=None, min_length=2, max_length=TITULO_MAXIMO)
    corpo: str | None = Field(default=None, min_length=5, max_length=CORPO_MAXIMO)
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
    corpo: str = Field(min_length=1, max_length=CORPO_MAXIMO)


class PreviewOut(BaseModel):
    resultado: str
