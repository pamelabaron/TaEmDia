"""Emissão e validação de tokens JWT (a "sessão" do vendedor após o login)."""
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"


def criar_access_token(vendedor_id: uuid.UUID) -> str:
    """Gera um JWT assinado contendo o id do vendedor e a data de expiração."""
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(vendedor_id), "exp": expira}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def validar_access_token(token: str) -> uuid.UUID | None:
    """Valida a assinatura e a expiração. Retorna o vendedor_id, ou None se inválido."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        return uuid.UUID(sub) if sub else None
    except (JWTError, ValueError):
        return None
