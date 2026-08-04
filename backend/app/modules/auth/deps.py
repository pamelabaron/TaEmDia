"""Dependência de autenticação: extrai e valida o JWT das requisições protegidas.
Garante que só vendedores autenticados acessem o sistema (RN01)."""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import validar_access_token

_bearer = HTTPBearer(auto_error=False)


def get_current_vendedor_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> uuid.UUID:
    """Retorna o vendedor_id do token, ou responde 401 se ausente/ inválido/ expirado."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    vendedor_id = validar_access_token(credentials.credentials)
    if vendedor_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return vendedor_id
