"""Acesso ao banco para templates de mensagem. Sempre filtra por vendedor_id."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.templates.models import TemplateMensagem


class TemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, vendedor_id: uuid.UUID) -> list[TemplateMensagem]:
        stmt = (
            select(TemplateMensagem)
            .where(TemplateMensagem.vendedor_id == vendedor_id)
            .order_by(TemplateMensagem.tipo)
        )
        return list(self.db.scalars(stmt))

    def buscar_por_id(self, vendedor_id: uuid.UUID, template_id: uuid.UUID) -> TemplateMensagem | None:
        stmt = select(TemplateMensagem).where(
            TemplateMensagem.id == template_id,
            TemplateMensagem.vendedor_id == vendedor_id,
        )
        return self.db.scalar(stmt)

    def buscar_por_tipo(self, vendedor_id: uuid.UUID, tipo: str) -> TemplateMensagem | None:
        stmt = select(TemplateMensagem).where(
            TemplateMensagem.vendedor_id == vendedor_id,
            TemplateMensagem.tipo == tipo,
        )
        return self.db.scalar(stmt)

    def criar_varios(self, templates: list[TemplateMensagem]) -> None:
        self.db.add_all(templates)
        self.db.commit()

    def salvar(self) -> None:
        self.db.commit()
