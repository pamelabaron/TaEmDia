"""Endpoints da assinatura: a tela do assinante e a conferência da administradora."""
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.assinatura import armazenamento
from app.modules.assinatura.deps import (
    eh_administrador,
    exigir_admin,
    get_assinatura_service,
)
from app.modules.assinatura.schemas import (
    MinhaAssinaturaOut,
    PagamentoOut,
    ComprovanteAdminOut,
    RecusaIn,
)
from app.modules.assinatura.service import (
    AssinaturaService,
    ComprovanteJaAvaliado,
    ComprovanteJaPendente,
    ComprovanteNaoEncontrado,
)
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.auth.repository import VendedorRepository

router = APIRouter(tags=["assinatura"])


# ---------------------------------------------------------------- assinante

@router.get("/assinatura", response_model=MinhaAssinaturaOut)
def minha_assinatura(
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
    service: AssinaturaService = Depends(get_assinatura_service),
    db: Session = Depends(get_db),
):
    """Situação da assinatura de quem está logado.

    Aberto a qualquer autenticado de propósito: é justamente quem está vencido
    que precisa ver esta tela. Para a administração a situação é "isenta": a
    validade gravada não se aplica, porque a trava nunca a bloqueia.
    """
    resumo = service.resumo(vendedor_id)
    isenta = eh_administrador(db, vendedor_id)
    return MinhaAssinaturaOut(
        situacao="isenta" if isenta else resumo["situacao"],
        valido_ate=resumo["valido_ate"],
        dias_restantes=resumo["dias_restantes"],
        tem_pendente=resumo["tem_pendente"],
        valor_mensal=settings.ASSINATURA_VALOR,
        pix_chave=settings.PIX_CHAVE,
        pix_nome=settings.PIX_NOME,
        historico=[PagamentoOut.model_validate(p) for p in resumo["historico"]],
    )


@router.post("/assinatura/comprovante", response_model=PagamentoOut, status_code=201)
async def enviar_comprovante(
    valor: float = Form(...),
    arquivo: UploadFile = File(...),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
    service: AssinaturaService = Depends(get_assinatura_service),
):
    """Envio do comprovante do Pix. Aberto a vencidos — é como se volta a ter acesso."""
    conteudo = await arquivo.read()
    try:
        tipo = armazenamento.validar(conteudo)
    except armazenamento.ArquivoInvalido as erro:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(erro))

    if valor <= 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Informe o valor pago.")

    caminho = armazenamento.guardar(conteudo, tipo)
    try:
        pagamento = service.registrar_comprovante(
            vendedor_id=vendedor_id,
            valor=valor,
            arquivo_nome=arquivo.filename or "comprovante",
            arquivo_caminho=caminho,
            arquivo_tipo=tipo,
        )
    except ComprovanteJaPendente:
        Path(caminho).unlink(missing_ok=True)
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Você já tem um comprovante em análise. Aguarde a conferência.",
        )
    return pagamento


# ------------------------------------------------------------ administradora

@router.get("/admin/comprovantes", response_model=list[ComprovanteAdminOut])
def listar_comprovantes(
    situacao: Literal["pendente", "aprovado", "recusado"] = "pendente",
    _admin: uuid.UUID = Depends(exigir_admin),
    service: AssinaturaService = Depends(get_assinatura_service),
    db: Session = Depends(get_db),
):
    """Fila de conferência (padrão) ou histórico de aprovados e recusados.

    Sem o filtro, devolve os pendentes, como antes: quem já chamava a fila
    continua recebendo a fila.
    """
    repo = VendedorRepository(db)
    saida = []
    for p in service.listar(situacao):
        vendedor = repo.buscar_por_id(p.vendedor_id)
        item = ComprovanteAdminOut.model_validate(p)
        item.vendedor_nome = vendedor.nome if vendedor else ""
        item.vendedor_email = vendedor.google_email if vendedor else ""
        saida.append(item)
    return saida


@router.get("/admin/comprovantes/{pagamento_id}/arquivo")
def baixar_comprovante(
    pagamento_id: uuid.UUID,
    _admin: uuid.UUID = Depends(exigir_admin),
    service: AssinaturaService = Depends(get_assinatura_service),
):
    """Entrega o arquivo. Único caminho de saída — a pasta não é servida como estática."""
    pagamento = service.pagamento_por_id(pagamento_id)
    if pagamento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comprovante não encontrado.")
    caminho = Path(pagamento.arquivo_caminho)
    if not caminho.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "O arquivo não está mais disponível.")
    return FileResponse(caminho, media_type=pagamento.arquivo_tipo,
                        filename=pagamento.arquivo_nome)


@router.post("/admin/comprovantes/{pagamento_id}/aprovar", response_model=PagamentoOut)
def aprovar_comprovante(
    pagamento_id: uuid.UUID,
    admin_id: uuid.UUID = Depends(exigir_admin),
    service: AssinaturaService = Depends(get_assinatura_service),
):
    """Aprova e estende a vigência em 30 dias (RN-A02)."""
    try:
        return service.aprovar(pagamento_id, admin_id)
    except ComprovanteNaoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comprovante não encontrado.")
    except ComprovanteJaAvaliado:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este comprovante já foi avaliado.")


@router.post("/admin/comprovantes/{pagamento_id}/recusar", response_model=PagamentoOut)
def recusar_comprovante(
    pagamento_id: uuid.UUID,
    dados: RecusaIn,
    admin_id: uuid.UUID = Depends(exigir_admin),
    service: AssinaturaService = Depends(get_assinatura_service),
):
    """Recusa sem alterar a vigência (RN-A03)."""
    try:
        return service.recusar(pagamento_id, admin_id, dados.motivo)
    except ComprovanteNaoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comprovante não encontrado.")
    except ComprovanteJaAvaliado:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este comprovante já foi avaliado.")
