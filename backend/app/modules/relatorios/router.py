"""Endpoints do dashboard, do ranking e da exportação de relatórios."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.clientes.repository import ClienteRepository
from app.modules.relatorios.pdf import gerar_pdf, montar_html
from app.modules.relatorios.repository import RelatorioDetalhadoRepository, RelatorioRepository
from app.modules.relatorios.schemas import DashboardOut, RankingOut
from app.modules.relatorios.service import RelatorioService
from app.modules.vendedores.models import Vendedor

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


@router.get("/pdf")
def exportar_pdf(
    desde: date | None = None,
    ate: date | None = None,
    db: Session = Depends(get_db),
    service: RelatorioService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    """Exporta o relatório financeiro do período em PDF (RF: exportar relatório)."""
    hoje = date.today()
    desde = desde or hoje.replace(day=1)
    ate = ate or hoje

    vendedor = db.get(Vendedor, vendedor_id)
    parcelas = RelatorioDetalhadoRepository(db).parcelas_no_periodo(vendedor_id, desde, ate)

    html = montar_html(
        vendedor_nome=vendedor.nome if vendedor else "",
        desde=desde, ate=ate,
        kpis=service.dashboard(vendedor_id),
        parcelas=parcelas, hoje=hoje,
    )
    nome = f"taemdia-relatorio-{desde:%Y%m%d}-{ate:%Y%m%d}.pdf"
    return Response(
        content=gerar_pdf(html),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
