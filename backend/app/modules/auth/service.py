"""Regras de autenticação: cria ou recupera o vendedor e emite o JWT (RF01/RF02)."""
from app.core.security import criar_access_token
from app.modules.auth.repository import VendedorRepository
from app.modules.vendedores.models import Vendedor


class AuthService:
    def __init__(self, repo: VendedorRepository):
        self.repo = repo

    def login_ou_cadastro(self, email: str, nome: str) -> tuple[Vendedor, str]:
        """Na primeira autenticação cria o vendedor; nas seguintes recupera. Retorna
        o vendedor e um JWT recém-emitido."""
        vendedor = self.repo.buscar_por_email(email)
        if vendedor is None:
            vendedor = self.repo.criar(email=email, nome=nome)
        token = criar_access_token(vendedor.id)
        return vendedor, token
