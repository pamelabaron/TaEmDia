"""Modelo (tabela) de Cliente. Ver docs/modelo-de-dados.md."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Cliente(Base):
    __tablename__ = "cliente"
    # Um mesmo número de WhatsApp não pode se repetir dentro da mesma conta (RF05/RN04).
    __table_args__ = (
        UniqueConstraint("vendedor_id", "whatsapp_numero", name="uq_cliente_vendedor_whatsapp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    whatsapp_numero: Mapped[str] = mapped_column(String, nullable=False)
    cpf: Mapped[str | None] = mapped_column(String, nullable=True)
    endereco: Mapped[str | None] = mapped_column(String, nullable=True)
    envio_auto_ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    interacao_habilitada: Mapped[bool] = mapped_column(Boolean, default=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)  # soft delete
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
