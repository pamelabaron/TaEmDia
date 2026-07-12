"""Repository: única camada que fala com o banco. Todo acesso filtra por vendedor_id
(isolamento entre contas — RNF07/RN02)."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.clientes.models import Cliente


class ClienteRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, vendedor_id: uuid.UUID) -> list[Cliente]:
        stmt = select(Cliente).where(
            Cliente.vendedor_id == vendedor_id, Cliente.ativo.is_(True)
        )
        return list(self.db.scalars(stmt))

    def buscar_por_id(self, vendedor_id: uuid.UUID, cliente_id: uuid.UUID) -> Cliente | None:
        stmt = select(Cliente).where(
            Cliente.id == cliente_id, Cliente.vendedor_id == vendedor_id
        )
        return self.db.scalar(stmt)

    def buscar_por_whatsapp(self, vendedor_id: uuid.UUID, numero: str) -> Cliente | None:
        stmt = select(Cliente).where(
            Cliente.vendedor_id == vendedor_id, Cliente.whatsapp_numero == numero
        )
        return self.db.scalar(stmt)

    def criar(self, cliente: Cliente) -> Cliente:
        self.db.add(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente

    def salvar(self, cliente: Cliente) -> Cliente:
        self.db.commit()
        self.db.refresh(cliente)
        return cliente
