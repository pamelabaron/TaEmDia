"""Endpoints das configurações do agente de cobrança."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.assinatura.deps import exigir_assinatura_ativa
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.configuracoes.repository import ConfiguracaoRepository
from app.modules.configuracoes.schemas import ConfiguracaoOut, ConfiguracaoUpdate
from app.modules.configuracoes.service import ConfiguracaoService

router = APIRouter(prefix="/configuracoes", tags=["configuracoes"])


def get_service(db: Session = Depends(get_db)) -> ConfiguracaoService:
    return ConfiguracaoService(ConfiguracaoRepository(db))


@router.get("", response_model=ConfiguracaoOut)
def obter_configuracoes(
    service: ConfiguracaoService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    """Configurações do vendedor. Na primeira vez, cria com os valores padrão."""
    return service.obter(vendedor_id)


@router.patch("", response_model=ConfiguracaoOut)
def atualizar_configuracoes(
    dados: ConfiguracaoUpdate,
    service: ConfiguracaoService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(exigir_assinatura_ativa),
):
    return service.atualizar(vendedor_id, dados)
