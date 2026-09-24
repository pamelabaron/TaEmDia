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
    # Derivado de ADMIN_EMAILS no servidor, nunca gravado no banco. Serve só
    # para o frontend decidir se mostra o item de menu: a porta de verdade é o
    # 403 que exigir_admin devolve.
    administrador: bool = False
