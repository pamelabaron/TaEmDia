"""Formatos de dados da autenticação."""
import uuid

from pydantic import BaseModel, ConfigDict


class TokenOut(BaseModel):
    """Resposta do login: o token JWT e como usá-lo."""
    access_token: str
    token_type: str = "bearer"


class VendedorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    google_email: str
    nome: str
    whatsapp_numero: str | None
