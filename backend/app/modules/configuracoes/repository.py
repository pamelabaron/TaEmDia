"""Acesso ao banco para as configurações do vendedor (uma por conta)."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.vendedores.models import Configuracao


class ConfiguracaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar(self, vendedor_id: uuid.UUID) -> Configuracao | None:
        return self.db.scalar(
            select(Configuracao).where(Configuracao.vendedor_id == vendedor_id)
        )

    def criar(self, vendedor_id: uuid.UUID) -> Configuracao:
        config = Configuracao(vendedor_id=vendedor_id)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def salvar(self) -> None:
        self.db.commit()
