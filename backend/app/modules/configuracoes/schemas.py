"""Formatos de dados das configurações do agente de cobrança."""
import uuid
from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

#: Por onde o resumo diário chega ao vendedor.
CanalResumo = Literal["whatsapp", "email", "ambos"]


class ConfiguracaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dias_antecedencia_lembrete: int
    horario_resumo: time
    resumo_ativo: bool
    envio_auto_global: bool
    canal_resumo: CanalResumo
    email_resumo: str | None = None
    whatsapp_resumo: str | None = None


class ConfiguracaoUpdate(BaseModel):
    """Campos editáveis. Todos opcionais: envia só o que mudou."""
    dias_antecedencia_lembrete: int | None = Field(
        default=None, ge=0, le=30,
        description="Dias de antecedência do lembrete (0 a 30).",
    )
    horario_resumo: time | None = None
    resumo_ativo: bool | None = None
    envio_auto_global: bool | None = None
    canal_resumo: CanalResumo | None = None
    #: O formato já é conferido pelo EmailStr; o tamanho não, e endereço de
    #: dez mil caracteres continua sendo um endereço válido para ele.
    email_resumo: EmailStr | None = Field(default=None, max_length=120)
    whatsapp_resumo: str | None = Field(
        default=None, max_length=20,
        description="WhatsApp que recebe o resumo. Vazio usa o número do agente.",
    )

    @field_validator("whatsapp_resumo")
    @classmethod
    def so_numeros(cls, valor: str | None) -> str | None:
        """Guarda só dígitos: quem digita costuma pôr parênteses e traço."""
        if valor is None:
            return None
        limpo = "".join(c for c in valor if c.isdigit())
        if not limpo:
            return None
        if len(limpo) < 10:
            raise ValueError("Informe o número com DDD.")
        return limpo

    @model_validator(mode="after")
    def exigir_endereco_quando_escolhe_email(self) -> "ConfiguracaoUpdate":
        """Escolher e-mail sem dizer para onde deixaria o resumo sem destino.

        A checagem vive aqui, e não na tela, porque a tela pode ser contornada:
        quem chamar a API direto também precisa informar o endereço.
        """
        if self.canal_resumo in ("email", "ambos") and not self.email_resumo:
            raise ValueError(
                "Informe o e-mail que vai receber o resumo."
            )
        return self
