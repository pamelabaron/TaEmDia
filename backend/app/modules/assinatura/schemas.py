"""Formatos de entrada e saída da assinatura."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PagamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    valor: float
    arquivo_nome: str
    situacao: str
    enviado_em: datetime
    avaliado_em: datetime | None = None
    observacao: str | None = None


class ComprovanteAdminOut(PagamentoOut):
    """O que a administração vê, na fila e no histórico."""

    vendedor_id: uuid.UUID
    vendedor_nome: str = ""
    vendedor_email: str = ""


class MinhaAssinaturaOut(BaseModel):
    situacao: str  # em_teste | ativa | vencida | isenta (administração)
    valido_ate: date | None
    dias_restantes: int
    tem_pendente: bool
    valor_mensal: float
    pix_chave: str
    pix_nome: str
    historico: list[PagamentoOut]


class RecusaIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=300)
