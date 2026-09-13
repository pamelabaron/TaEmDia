"""A trava de escrita e o acesso de administradora.

Estas duas dependências são o ponto único onde o acesso pago é decidido. A
verificação acontece **no servidor**, a partir do token assinado: esconder um
botão no navegador é conforto visual, não segurança.

Ver docs/superpowers/specs/2026-09-13-assinatura-design.md, seções 2 e 3.
"""
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.assinatura.repository import AssinaturaRepository
from app.modules.assinatura.service import AssinaturaService
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.auth.repository import VendedorRepository


def get_assinatura_service(db: Session = Depends(get_db)) -> AssinaturaService:
    return AssinaturaService(AssinaturaRepository(db))


def exigir_assinatura_ativa(
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
    service: AssinaturaService = Depends(get_assinatura_service),
) -> uuid.UUID:
    """Libera a escrita apenas para quem está em teste ou com assinatura ativa.

    Responde **402 Pagamento Necessário** — o código existe exatamente para
    este caso, e deixa o tratamento no frontend uniforme.
    """
    if not service.pode_escrever(vendedor_id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Sua assinatura venceu. Renove para continuar usando o sistema.",
        )
    return vendedor_id


def exigir_admin(
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
    db: Session = Depends(get_db),
) -> uuid.UUID:
    """Restringe a conferência de comprovantes aos e-mails de ADMIN_EMAILS."""
    vendedor = VendedorRepository(db).buscar_por_id(vendedor_id)
    email = (vendedor.google_email or "").lower() if vendedor else ""
    if not email or email not in settings.administradores:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito à administração.",
        )
    return vendedor_id
