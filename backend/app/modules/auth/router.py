"""Endpoints de autenticação via Google OAuth 2.0 (UC01)."""
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.auth.google_client import montar_url_de_login, trocar_codigo_por_usuario
from app.modules.auth.repository import VendedorRepository
from app.modules.auth.schemas import VendedorOut
from app.modules.auth.service import AuthService
from app.modules.vendedores.models import Vendedor

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
def login_google():
    """Redireciona o vendedor para a tela de autorização do Google."""
    return RedirectResponse(montar_url_de_login())


@router.get("/google/callback")
async def callback_google(code: str, db: Session = Depends(get_db)):
    """Recebe o retorno do Google, cria/recupera o vendedor, emite o JWT e
    redireciona de volta ao frontend com o token."""
    try:
        userinfo = await trocar_codigo_por_usuario(code)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha ao autenticar com o Google. Tente novamente.",
        )

    email = userinfo.get("email")
    nome = userinfo.get("name") or email
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conta Google sem e-mail disponível.",
        )

    service = AuthService(VendedorRepository(db))
    _, token = service.login_ou_cadastro(email=email, nome=nome)
    # O token vai no "fragmento" da URL (#), que não é enviado a servidores — o
    # Angular lê e guarda localmente.
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback#token={token}")


@router.get("/me", response_model=VendedorOut)
def dados_do_vendedor_logado(
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
    db: Session = Depends(get_db),
):
    """Retorna os dados do vendedor autenticado (útil para o frontend)."""
    vendedor = db.get(Vendedor, vendedor_id)
    if vendedor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendedor não encontrado.")
    return vendedor
