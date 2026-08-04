"""Endpoints dos templates de mensagem de cobrança."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.schemas import (
    PreviewIn, PreviewOut, TemplateOut, TemplateUpdate,
)
from app.modules.templates.service import TemplateNaoEncontradoError, TemplateService, VARIAVEIS

router = APIRouter(prefix="/templates", tags=["templates"])


def get_service(db: Session = Depends(get_db)) -> TemplateService:
    return TemplateService(TemplateRepository(db))


@router.get("", response_model=list[TemplateOut])
def listar_templates(
    service: TemplateService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    """Lista os templates do vendedor. Na primeira vez, cria os 3 padrão."""
    return service.listar(vendedor_id)


@router.get("/variaveis", response_model=list[str])
def variaveis_disponiveis():
    """Lista as variáveis dinâmicas que podem ser usadas nos templates."""
    return VARIAVEIS


@router.post("/preview", response_model=PreviewOut)
def preview(
    dados: PreviewIn,
    service: TemplateService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    """Mostra como a mensagem fica com dados de exemplo."""
    return PreviewOut(resultado=service.preview(dados.corpo))


@router.patch("/{template_id}", response_model=TemplateOut)
def editar_template(
    template_id: uuid.UUID,
    dados: TemplateUpdate,
    service: TemplateService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    try:
        return service.editar(vendedor_id, template_id, dados)
    except TemplateNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template não encontrado.")
