"""Tabelas da assinatura. Ver docs/superpowers/specs/2026-09-13-assinatura-design.md.

Observe que **não existe coluna de status**: a situação é derivada das datas
por `regras.situacao()`. Ver docs/modelo-de-dados.md.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Assinatura(Base):
    """Vigência atual do acesso de escrita. Uma linha por vendedor."""

    __tablename__ = "assinatura"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, unique=True, nullable=False
    )
    valido_ate: Mapped[date] = mapped_column(Date, nullable=False)
    origem: Mapped[str] = mapped_column(String, nullable=False)  # "teste" | "pago"
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class PagamentoAssinatura(Base):
    """Comprovante enviado por Pix e o resultado da conferência."""

    __tablename__ = "pagamento_assinatura"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Nome original só para exibição. O caminho no disco é gerado pelo sistema:
    # nome enviado pelo usuário nunca entra na formação de caminho.
    arquivo_nome: Mapped[str] = mapped_column(String, nullable=False)
    arquivo_caminho: Mapped[str] = mapped_column(String, nullable=False)
    arquivo_tipo: Mapped[str] = mapped_column(String, nullable=False)

    situacao: Mapped[str] = mapped_column(
        String, nullable=False, default="pendente"
    )  # "pendente" | "aprovado" | "recusado"
    enviado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    avaliado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    avaliado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    observacao: Mapped[str | None] = mapped_column(String, nullable=True)
