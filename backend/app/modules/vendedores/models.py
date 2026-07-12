"""Modelos de Vendedor (dono da conta) e sua Configuração. Ver docs/modelo-de-dados.md."""
import uuid
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Vendedor(Base):
    __tablename__ = "vendedor"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    whatsapp_numero: Mapped[str | None] = mapped_column(String, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Configuracao(Base):
    """Preferências do agente de cobrança, uma por vendedor (1-para-1)."""
    __tablename__ = "configuracao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendedor.id"), unique=True, nullable=False
    )
    dias_antecedencia_lembrete: Mapped[int] = mapped_column(Integer, default=3)
    horario_resumo: Mapped[time] = mapped_column(Time, default=time(20, 0))
    resumo_ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    envio_auto_global: Mapped[bool] = mapped_column(Boolean, default=True)
