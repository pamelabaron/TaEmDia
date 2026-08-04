"""Modelo de Template de Mensagem de cobrança. Ver docs/modelo-de-dados.md."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TemplateMensagem(Base):
    __tablename__ = "template_mensagem"
    # Um template por tipo (lembrete/vencimento/atraso) por vendedor.
    __table_args__ = (
        UniqueConstraint("vendedor_id", "tipo", name="uq_template_vendedor_tipo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)  # lembrete | vencimento | atraso
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    corpo: Mapped[str] = mapped_column(Text, nullable=False)
    is_padrao: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
