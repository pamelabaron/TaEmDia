"""Formatos de dados das configurações do agente de cobrança."""
import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class ConfiguracaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dias_antecedencia_lembrete: int
    horario_resumo: time
    resumo_ativo: bool
    envio_auto_global: bool


class ConfiguracaoUpdate(BaseModel):
    """Campos editáveis. Todos opcionais: envia só o que mudou."""
    dias_antecedencia_lembrete: int | None = Field(
        default=None, ge=0, le=30,
        description="Dias de antecedência do lembrete (0 a 30).",
    )
    horario_resumo: time | None = None
    resumo_ativo: bool | None = None
    envio_auto_global: bool | None = None
