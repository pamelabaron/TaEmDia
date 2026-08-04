"""Acesso ao banco para vendas e parcelas. Sempre filtra por vendedor_id (isolamento)."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.vendas.models import Parcela, Venda


class VendaRepository:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, venda: Venda) -> Venda:
        self.db.add(venda)
        self.db.commit()
        self.db.refresh(venda)
        return venda

    def buscar_por_id(self, vendedor_id: uuid.UUID, venda_id: uuid.UUID) -> Venda | None:
        stmt = (
            select(Venda)
            .where(Venda.id == venda_id, Venda.vendedor_id == vendedor_id)
            .options(selectinload(Venda.parcelas))
        )
        return self.db.scalar(stmt)

    def listar_por_cliente(self, vendedor_id: uuid.UUID, cliente_id: uuid.UUID) -> list[Venda]:
        stmt = (
            select(Venda)
            .where(Venda.vendedor_id == vendedor_id, Venda.cliente_id == cliente_id)
            .options(selectinload(Venda.parcelas))
            .order_by(Venda.criado_em.desc())
        )
        return list(self.db.scalars(stmt))

    def salvar(self) -> None:
        self.db.commit()


class ParcelaRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_id(self, vendedor_id: uuid.UUID, parcela_id: uuid.UUID) -> Parcela | None:
        """Busca a parcela garantindo, via JOIN com a venda, que pertence ao vendedor."""
        stmt = (
            select(Parcela)
            .join(Venda, Parcela.venda_id == Venda.id)
            .where(Parcela.id == parcela_id, Venda.vendedor_id == vendedor_id)
        )
        return self.db.scalar(stmt)

    def salvar(self) -> None:
        self.db.commit()
