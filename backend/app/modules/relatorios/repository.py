"""Consultas agregadas para o dashboard financeiro. Tudo filtrado por vendedor_id.
Usa SUM/COUNT no banco (RNF: operações rápidas)."""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.clientes.models import Cliente
from app.modules.vendas.models import Parcela, Venda


class RelatorioRepository:
    def __init__(self, db: Session):
        self.db = db

    def _base_parcelas_abertas(self, vendedor_id: uuid.UUID):
        """Parcelas não pagas de vendas ativas."""
        return (
            select(func.coalesce(func.sum(Parcela.valor), 0))
            .select_from(Parcela)
            .join(Venda, Parcela.venda_id == Venda.id)
            .where(
                Venda.vendedor_id == vendedor_id,
                Venda.status == "ativa",
                Parcela.data_pagamento.is_(None),
            )
        )

    def total_a_receber(self, vendedor_id: uuid.UUID) -> Decimal:
        return self.db.scalar(self._base_parcelas_abertas(vendedor_id)) or Decimal("0")

    def em_atraso(self, vendedor_id: uuid.UUID, hoje: date) -> Decimal:
        stmt = self._base_parcelas_abertas(vendedor_id).where(Parcela.data_vencimento < hoje)
        return self.db.scalar(stmt) or Decimal("0")

    def recebido_no_mes(self, vendedor_id: uuid.UUID, inicio_mes: date) -> Decimal:
        stmt = (
            select(func.coalesce(func.sum(Parcela.valor), 0))
            .select_from(Parcela)
            .join(Venda, Parcela.venda_id == Venda.id)
            .where(
                Venda.vendedor_id == vendedor_id,
                Parcela.data_pagamento.is_not(None),
                Parcela.data_pagamento >= inicio_mes,
            )
        )
        return self.db.scalar(stmt) or Decimal("0")

    def clientes_inadimplentes(self, vendedor_id: uuid.UUID, hoje: date) -> int:
        stmt = (
            select(func.count(func.distinct(Venda.cliente_id)))
            .select_from(Parcela)
            .join(Venda, Parcela.venda_id == Venda.id)
            .where(
                Venda.vendedor_id == vendedor_id,
                Venda.status == "ativa",
                Parcela.data_pagamento.is_(None),
                Parcela.data_vencimento < hoje,
            )
        )
        return self.db.scalar(stmt) or 0

    def recebimentos_mensais(self, vendedor_id: uuid.UUID, desde: date) -> list[tuple[str, Decimal]]:
        mes = func.to_char(Parcela.data_pagamento, "YYYY-MM")
        stmt = (
            select(mes.label("mes"), func.coalesce(func.sum(Parcela.valor), 0))
            .select_from(Parcela)
            .join(Venda, Parcela.venda_id == Venda.id)
            .where(
                Venda.vendedor_id == vendedor_id,
                Parcela.data_pagamento.is_not(None),
                Parcela.data_pagamento >= desde,
            )
            .group_by(mes)
            .order_by(mes)
        )
        return [(linha[0], linha[1]) for linha in self.db.execute(stmt)]

    def clientes_em_atraso(self, vendedor_id: uuid.UUID, hoje: date) -> list[tuple[uuid.UUID, str, Decimal]]:
        total = func.sum(Parcela.valor)
        stmt = (
            select(Cliente.id, Cliente.nome, total.label("valor"))
            .select_from(Parcela)
            .join(Venda, Parcela.venda_id == Venda.id)
            .join(Cliente, Venda.cliente_id == Cliente.id)
            .where(
                Venda.vendedor_id == vendedor_id,
                Venda.status == "ativa",
                Parcela.data_pagamento.is_(None),
                Parcela.data_vencimento < hoje,
            )
            .group_by(Cliente.id, Cliente.nome)
            .order_by(total.desc())
        )
        return [(l[0], l[1], l[2]) for l in self.db.execute(stmt)]
