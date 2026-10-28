"""Schemas Pydantic: definem o formato dos dados que entram e saem da API."""
import uuid
from datetime import datetime

from pydantic import (
    BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator,
)

from .regras import (
    CODIGO_PAIS_PADRAO,
    ENDERECO_MAXIMO,
    NOME_MAXIMO,
    NOME_MINIMO,
    formatar_telefone,
    normalizar_cpf,
    normalizar_telefone,
)


class ClienteCreate(BaseModel):
    """Dados para cadastrar um cliente (RF04).

    A validação de CPF e telefone acontece aqui, e não só no formulário,
    porque o formulário pode ser contornado por quem chamar a API direto.
    """
    nome: str = Field(min_length=NOME_MINIMO, max_length=NOME_MAXIMO)
    #: Cabe "+55 (47) 99999-0000" com pontuação; a regra confere o conteúdo.
    whatsapp_numero: str = Field(min_length=8, max_length=24)
    #: Editável, mas nasce no Brasil. Fica fora do banco: o número já é
    #: guardado com o código do país na frente.
    codigo_pais: str = Field(default=CODIGO_PAIS_PADRAO, max_length=5)
    #: Cabe "529.982.247-25" com pontuação.
    cpf: str | None = Field(default=None, max_length=14)
    endereco: str | None = Field(default=None, max_length=ENDERECO_MAXIMO)

    @field_validator("cpf")
    @classmethod
    def conferir_cpf(cls, valor: str | None) -> str | None:
        return normalizar_cpf(valor)

    @model_validator(mode="after")
    def conferir_whatsapp(self) -> "ClienteCreate":
        """Depende de dois campos, por isso não é um field_validator.

        O número é guardado pronto para envio: código do país, DDD e número.
        """
        self.whatsapp_numero = normalizar_telefone(
            self.whatsapp_numero, self.codigo_pais
        )
        return self


class ClienteUpdate(BaseModel):
    """Campos editáveis de um cliente (RF06). Todos opcionais.

    O WhatsApp não entra: ele identifica o cliente dentro da carteira
    (restrição de unicidade no banco). Trocar de número é cadastrar de novo.
    """
    nome: str | None = Field(default=None, min_length=NOME_MINIMO, max_length=NOME_MAXIMO)
    cpf: str | None = Field(default=None, max_length=14)
    endereco: str | None = Field(default=None, max_length=ENDERECO_MAXIMO)
    envio_auto_ativo: bool | None = None
    interacao_habilitada: bool | None = None

    @field_validator("cpf")
    @classmethod
    def conferir_cpf(cls, valor: str | None) -> str | None:
        return normalizar_cpf(valor)


class ClienteOut(BaseModel):
    """Formato de saída de um cliente."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    whatsapp_numero: str
    cpf: str | None
    endereco: str | None
    envio_auto_ativo: bool
    interacao_habilitada: bool
    ativo: bool
    criado_em: datetime

    @computed_field
    @property
    def whatsapp_formatado(self) -> str:
        """Como o número aparece na tela: "55 (47) 99999-0000".

        Vem pronto da API para que a tela não repita a regra de formatação
        e as duas nunca discordem.
        """
        return formatar_telefone(self.whatsapp_numero)
