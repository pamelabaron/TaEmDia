"""Endpoints do dashboard, do ranking e da exportação de relatórios."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.clientes.repository import ClienteRepository
from app.modules.cobrancas.router import get_agente_service
from app.modules.agente.service import AgenteService
from app.modules.relatorios.pdf import gerar_pdf, montar_html, montar_html_resumo
from app.modules.relatorios.resumo import (
    DIAS_DA_JANELA,
    ROTULO_OPCAO,
    dentro_da_janela,
    dias_da_janela,
)
from app.modules.relatorios.repository import RelatorioDetalhadoRepository, RelatorioRepository
from app.modules.relatorios.schemas import DashboardOut, RankingOut, ResumoDoDiaOut
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


# ------------------------------------------------------------- resumo do dia

def _dia_valido(dia: date | None) -> date:
    """Aplica a janela de 7 dias (RN-R01) antes de qualquer consulta.

    Fica aqui, e não na tela, porque a tela pode ser contornada: quem chamar a
    API direto também esbarra no limite.
    """
    escolhido = dia or date.today()
    if not dentro_da_janela(escolhido, date.today()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"O resumo cobre apenas os últimos {DIAS_DA_JANELA} dias.",
        )
    return escolhido


@router.get("/resumo/dias", response_model=list[date])
def dias_do_resumo(_vendedor_id: uuid.UUID = Depends(get_current_vendedor_id)):
    """As datas que o filtro pode oferecer, da mais recente para a mais antiga."""
    return dias_da_janela(date.today())


@router.get("/resumo", response_model=ResumoDoDiaOut)
def resumo_do_dia(
    dia: date | None = None,
    agente: AgenteService = Depends(get_agente_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    """Os números de um dia. Leitura: quem está com a assinatura vencida
    continua consultando o que já aconteceu."""
    escolhido = _dia_valido(dia)
    r = agente.dados_do_resumo(vendedor_id, escolhido)
    return ResumoDoDiaOut(
        dia=r.dia,
        houve_atividade=r.houve_atividade,
        cobrancas_enviadas=r.cobrancas_enviadas,
        cobrancas_falharam=r.cobrancas_falharam,
        pagamentos=r.pagamentos,
        valor_recebido=r.valor_recebido,
        sem_resposta=r.sem_resposta,
        respostas=r.respostas,
        rotulos=ROTULO_OPCAO,
    )


@router.get("/resumo/pdf")
def resumo_em_pdf(
    dia: date | None = None,
    agente: AgenteService = Depends(get_agente_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
    db: Session = Depends(get_db),
):
    """O mesmo resumo, em PDF, para guardar ou anexar."""
    escolhido = _dia_valido(dia)
    r = agente.dados_do_resumo(vendedor_id, escolhido)
    vendedor = db.get(Vendedor, vendedor_id)
    html = montar_html_resumo(r, ROTULO_OPCAO, vendedor.nome if vendedor else "")
    return Response(
        content=gerar_pdf(html),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="resumo-{escolhido.isoformat()}.pdf"'
        },
    )
