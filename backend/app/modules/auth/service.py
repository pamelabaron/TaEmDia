"""Regras de autenticação: cria ou recupera o vendedor e emite o JWT (RF01/RF02)."""
from app.core.security import criar_access_token
from app.modules.assinatura.repository import AssinaturaRepository
from app.modules.assinatura.service import AssinaturaService
from app.modules.auth.repository import VendedorRepository
from app.modules.vendedores.models import Vendedor


class AuthService:
    def __init__(self, repo: VendedorRepository):
        self.repo = repo

    def login_ou_cadastro(
        self, email: str, nome: str, foto_url: str | None = None
    ) -> tuple[Vendedor, str]:
        """Na primeira autenticação cria o vendedor; nas seguintes recupera. Retorna
        o vendedor e um JWT recém-emitido.

        A foto acompanha o Google a cada login: trocou lá, troca aqui; tirou lá,
        some aqui. A tela mostra a conta como ela é hoje, e guardar a foto antiga
        faria o sistema exibir algo que não existe mais.
        """
        vendedor = self.repo.buscar_por_email(email)
        if vendedor is None:
            vendedor = self.repo.criar(email=email, nome=nome, foto_url=foto_url)
            # Conta nova começa com os dias de teste (RN-A01).
            AssinaturaService(AssinaturaRepository(self.repo.db)).iniciar_teste(vendedor.id)
        elif vendedor.foto_url != foto_url:
            vendedor.foto_url = foto_url
            self.repo.salvar()
        token = criar_access_token(vendedor.id)
        return vendedor, token
