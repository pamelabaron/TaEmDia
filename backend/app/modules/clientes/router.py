"""Router: expõe os endpoints HTTP de clientes e delega ao Service."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import get_current_vendedor_id
from app.modules.clientes.repository import ClienteRepository
from app.modules.clientes.schemas import ClienteCreate, ClienteOut, ClienteUpdate
from app.modules.clientes.service import (
    ClienteNaoEncontradoError,
    ClienteService,
    WhatsappDuplicadoError,
)

router = APIRouter(prefix="/clientes", tags=["clientes"])


def get_service(db: Session = Depends(get_db)) -> ClienteService:
    return ClienteService(ClienteRepository(db))


@router.get("", response_model=list[ClienteOut])
def listar_clientes(
    service: ClienteService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    return service.listar(vendedor_id)


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def cadastrar_cliente(
    dados: ClienteCreate,
    service: ClienteService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    try:
        return service.cadastrar(vendedor_id, dados)
    except WhatsappDuplicadoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um cliente com esse número de WhatsApp nesta conta.",
        )


@router.patch("/{cliente_id}", response_model=ClienteOut)
def editar_cliente(
    cliente_id: uuid.UUID,
    dados: ClienteUpdate,
    service: ClienteService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    try:
        return service.editar(vendedor_id, cliente_id, dados)
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_cliente(
    cliente_id: uuid.UUID,
    service: ClienteService = Depends(get_service),
    vendedor_id: uuid.UUID = Depends(get_current_vendedor_id),
):
    try:
        service.desativar(vendedor_id, cliente_id)
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
