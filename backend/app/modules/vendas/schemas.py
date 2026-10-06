"""Formatos de dados de vendas e parcelas."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from ..clientes.regras import formatar_cpf, formatar_telefone

#: Teto do valor de uma venda. Carnê de loja não passa disso, e o teto pega o
#: erro de quem digita 50000 quando queria 500,00: sem ele, o agente cobraria
#: cinquenta mil reais de verdade, por WhatsApp, sozinho.
VALOR_MAXIMO_DA_VENDA = 1_000_000.0

#: Faixa aceita para a data da primeira parcela, contada a partir de hoje.
#: Um ano para trás porque lançar hoje a venda do mês passado é rotina; cinco
#: anos para a frente porque parcelamento longo existe. Fora disso é sempre
#: engano de digitação, como o ano 9999 que o calendário aceita calado.
ANOS_PARA_TRAS = 1
ANOS_PARA_FRENTE = 5


class VendaCreate(BaseModel):
    """Dados para registrar uma venda parcelada (RF09)."""
    cliente_id: uuid.UUID
    valor_total: float = Field(
        gt=0, le=VALOR_MAXIMO_DA_VENDA,
        description=f"Valor total, de R$ 0,01 a R$ {VALOR_MAXIMO_DA_VENDA:,.0f} (RN06).",
    )
    num_parcelas: int = Field(ge=1, le=60, description="Entre 1 e 60 (RN07).")
    data_primeira_parcela: date

    @field_validator("data_primeira_parcela")
    @classmethod
    def conferir_data(cls, valor: date) -> date:
        """Data fora da faixa é engano, não carnê (RN-L01)."""
        hoje = date.today()
        primeira = hoje.replace(year=hoje.year - ANOS_PARA_TRAS)
        ultima = hoje.replace(year=hoje.year + ANOS_PARA_FRENTE)
        if not primeira <= valor <= ultima:
            raise ValueError(
                f"A data precisa ficar entre {primeira:%d/%m/%Y} e {ultima:%d/%m/%Y}."
            )
        return valor


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

    @computed_field
    @property
    def whatsapp_formatado(self) -> str:
        """Mesma formatação da listagem de clientes (RN-C01)."""
        return formatar_telefone(self.whatsapp_numero)

    @computed_field
    @property
    def cpf_formatado(self) -> str:
        return formatar_cpf(self.cpf)
