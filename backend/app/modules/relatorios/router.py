"""Endpoint do dashboard financeiro (RF: indicadores e relatórios)."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.clientes.repository import ClienteRepository
from app.modules.relatorios.repository import RelatorioRepository
from app.modules.relatorios.schemas import DashboardOut, RankingOut
from app.modules.relatorios.service import RelatorioService

router = APIRouter(prefix="/relatorios", tags=["relatorios"])


def get_service(db: Session = Depends(get_db)) -> RelatorioService:
    return RelatorioService(RelatorioRepository(db), ClienteRepository(db))


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    service: RelatorioService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    return service.dashboard(vendedor_id)


@router.get("/ranking", response_model=RankingOut)
def ranking(
    meses: int = 12,
    service: RelatorioService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    return service.ranking(vendedor_id, meses)
