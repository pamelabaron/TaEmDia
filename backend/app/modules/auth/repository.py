"""Acesso ao banco para vendedores (usado na autenticação)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.vendedores.models import Vendedor


class VendedorRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_email(self, email: str) -> Vendedor | None:
        return self.db.scalar(select(Vendedor).where(Vendedor.google_email == email))

    def criar(self, email: str, nome: str) -> Vendedor:
        vendedor = Vendedor(google_email=email, nome=nome)
        self.db.add(vendedor)
        self.db.commit()
        self.db.refresh(vendedor)
        return vendedor
