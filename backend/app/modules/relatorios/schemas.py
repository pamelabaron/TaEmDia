"""Formatos de saída do dashboard."""
import uuid

from pydantic import BaseModel


class RecebimentoMes(BaseModel):
    mes: str  # "2026-08"
    total: float


class ClienteEmAtraso(BaseModel):
    id: uuid.UUID
    nome: str
    valor_atrasado: float


class DashboardOut(BaseModel):
    total_a_receber: float
    recebido_no_mes: float
    em_atraso: float
    clientes_inadimplentes: int
    recebimentos_mensais: list[RecebimentoMes]
    clientes_em_atraso: list[ClienteEmAtraso]


class RankingClienteOut(BaseModel):
    id: uuid.UUID
    nome: str
    classificacao: str  # bom | regular | inadimplente | sem_historico
    percentual_em_dia: float
    media_dias_atraso: float
    total_avaliadas: int


class RankingOut(BaseModel):
    bons: int
    regulares: int
    inadimplentes: int
    sem_historico: int
    clientes: list[RankingClienteOut]
