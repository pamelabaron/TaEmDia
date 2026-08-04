"""Formatos de dados de vendas e parcelas."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class VendaCreate(BaseModel):
    """Dados para registrar uma venda parcelada (RF09)."""
    cliente_id: uuid.UUID
    valor_total: float = Field(gt=0, description="Valor total; mínimo R$ 1,00 (RN06).")
    num_parcelas: int = Field(ge=1, le=60, description="Entre 1 e 60 (RN07).")
    data_primeira_parcela: date


class ParcelaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numero_parcela: int
    valor: float
    data_vencimento: date
    data_pagamento: date | None
    status: str  # pendente | atrasada | aguardando_confirmacao | paga


class VendaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cliente_id: uuid.UUID
    valor_total: float
    num_parcelas: int
    data_primeira_parcela: date
    status: str
    criado_em: datetime
    parcelas: list[ParcelaOut]


class PerfilClienteOut(BaseModel):
    """Perfil do cliente com histórico e saldo devedor (RF07/RF08)."""
    id: uuid.UUID
    nome: str
    whatsapp_numero: str
    cpf: str | None
    endereco: str | None
    saldo_devedor: float
    vendas: list[VendaOut]
