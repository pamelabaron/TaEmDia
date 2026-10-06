"""Modelos do log de cobranças e das respostas dos devedores.
Ver docs/modelo-de-dados.md."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CobrancaLog(Base):
    """Registro de cada mensagem de cobrança enviada (ou tentada)."""
    __tablename__ = "cobranca_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cliente.id"), index=True, nullable=True
    )
    parcela_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcela.id"), index=True, nullable=True
    )
    # lembrete | vencimento | atraso | manual | resumo | automatica
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    # enviado | falhou | pendente (pendente = fila de reenvio)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pendente")
    detalhe: Mapped[str | None] = mapped_column(String, nullable=True)
    enviado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class RespostaDevedor(Base):
    """Resposta numerada (1/2/3) recebida do devedor pelo WhatsApp."""
    __tablename__ = "resposta_devedor"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cliente.id"), index=True, nullable=False
    )
    parcela_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcela.id"), index=True, nullable=True
    )
    # 1_ja_paguei | 2_pago_hoje | 3_nao_consigo
    opcao: Mapped[str] = mapped_column(String, nullable=False)
    recebido_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
