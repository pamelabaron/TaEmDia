"""Endpoints de vendas, parcelas e perfil do cliente."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.clientes.repository import ClienteRepository
from app.modules.vendas.repository import ParcelaRepository, VendaRepository
from app.modules.vendas.schemas import PerfilClienteOut, VendaCreate, VendaOut, ParcelaOut
from app.modules.vendas.service import (
    ClienteInexistenteError,
    OperacaoInvalidaError,
    ParcelaNaoEncontradaError,
    VendaNaoEncontradaError,
    VendasService,
    calcular_status,
    venda_para_dict,
)

router = APIRouter(tags=["vendas"])


def get_service(db: Session = Depends(get_db)) -> VendasService:
    return VendasService(VendaRepository(db), ParcelaRepository(db), ClienteRepository(db))


@router.post("/vendas", response_model=VendaOut, status_code=status.HTTP_201_CREATED)
def registrar_venda(
    dados: VendaCreate,
    service: VendasService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    try:
        venda = service.registrar_venda(
            vendedor_id, dados.cliente_id, dados.valor_total,
            dados.num_parcelas, dados.data_primeira_parcela,
        )
    except ClienteInexistenteError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    return venda_para_dict(venda)


@router.get("/vendas/{venda_id}", response_model=VendaOut)
def obter_venda(
    venda_id: uuid.UUID,
    service: VendasService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    try:
        return venda_para_dict(service.obter_venda(vendedor_id, venda_id))
    except VendaNaoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada.")


@router.post("/parcelas/{parcela_id}/pagar", response_model=ParcelaOut)
def confirmar_pagamento(
    parcela_id: uuid.UUID,
    service: VendasService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    try:
        parcela = service.confirmar_pagamento(vendedor_id, parcela_id)
    except ParcelaNaoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela não encontrada.")
    except OperacaoInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.mensagem)
    return {
        "id": parcela.id,
        "numero_parcela": parcela.numero_parcela,
        "valor": float(parcela.valor),
        "data_vencimento": parcela.data_vencimento,
        "data_pagamento": parcela.data_pagamento,
        "status": calcular_status(parcela),
    }


@router.post("/vendas/{venda_id}/cancelar", response_model=VendaOut)
def cancelar_venda(
    venda_id: uuid.UUID,
    service: VendasService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    try:
        venda = service.cancelar_venda(vendedor_id, venda_id)
    except VendaNaoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada.")
    except OperacaoInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.mensagem)
    return venda_para_dict(venda)


@router.get("/clientes/{cliente_id}/perfil", response_model=PerfilClienteOut)
def perfil_do_cliente(
    cliente_id: uuid.UUID,
    service: VendasService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    try:
        return service.obter_perfil(vendedor_id, cliente_id)
    except ClienteInexistenteError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
