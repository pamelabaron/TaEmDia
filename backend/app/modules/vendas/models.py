"""Modelos de Venda e Parcela. Ver docs/modelo-de-dados.md.

O status da parcela NÃO é armazenado: é derivado da data de vencimento, da data de
pagamento e do sinalizador de confirmação (ver service.calcular_status). Isso garante
que o status esteja sempre correto conforme a data atual (RN09), sem depender de um job.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Venda(Base):
    __tablename__ = "venda"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cliente.id"), index=True, nullable=False
    )
    valor_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    num_parcelas: Mapped[int] = mapped_column(Integer, nullable=False)
    data_primeira_parcela: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, default="ativa")  # ativa | cancelada
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    parcelas: Mapped[list["Parcela"]] = relationship(
        back_populates="venda", cascade="all, delete-orphan", order_by="Parcela.numero_parcela"
    )


class Parcela(Base):
    __tablename__ = "parcela"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venda_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("venda.id"), index=True, nullable=False
    )
    numero_parcela: Mapped[int] = mapped_column(Integer, nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    aguardando_confirmacao: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    venda: Mapped["Venda"] = relationship(back_populates="parcelas")
