"""A foto do perfil vem do Google e precisa sobreviver ao login seguinte.

O Google devolve a foto junto com nome e e-mail a cada autenticação, e o que
está guardado aqui acompanha isso em todo login: trocou lá, troca aqui; tirou
lá, some aqui. A tela mostra a realidade da conta, não o histórico dela.
"""
import pytest

from app.modules.auth.repository import VendedorRepository
from app.modules.auth.service import AuthService

FOTO = "https://lh3.googleusercontent.com/a/exemplo=s96-c"
OUTRA_FOTO = "https://lh3.googleusercontent.com/a/nova=s96-c"


@pytest.fixture()
def servico(db) -> AuthService:
    return AuthService(VendedorRepository(db))


def test_conta_nova_guarda_a_foto(servico):
    vendedor, _ = servico.login_ou_cadastro(
        email="nova@exemplo.com", nome="Nova", foto_url=FOTO)
    assert vendedor.foto_url == FOTO


def test_login_seguinte_atualiza_a_foto(servico):
    servico.login_ou_cadastro(email="mesma@exemplo.com", nome="Mesma", foto_url=FOTO)
    vendedor, _ = servico.login_ou_cadastro(
        email="mesma@exemplo.com", nome="Mesma", foto_url=OUTRA_FOTO)
    assert vendedor.foto_url == OUTRA_FOTO


def test_login_sem_foto_apaga_a_que_existia(servico):
    """Quem tirou a foto do Google deixa de ter foto aqui também.

    A tela mostra o que a conta tem hoje, não o que já teve: guardar a foto
    antiga faria o sistema exibir algo que não existe mais no Google.
    """
    servico.login_ou_cadastro(email="semfoto@exemplo.com", nome="Sem", foto_url=FOTO)
    vendedor, _ = servico.login_ou_cadastro(
        email="semfoto@exemplo.com", nome="Sem", foto_url=None)
    assert vendedor.foto_url is None


def test_conta_sem_foto_nenhuma_fica_nula(servico):
    vendedor, _ = servico.login_ou_cadastro(
        email="anonima@exemplo.com", nome="Anônima", foto_url=None)
    assert vendedor.foto_url is None


def test_a_api_devolve_a_foto(cliente_http, db):
    """O /auth/me alimenta o bloco da pessoa na barra lateral."""
    from app.core.security import criar_access_token

    vendedor, _ = AuthService(VendedorRepository(db)).login_ou_cadastro(
        email="perfil@exemplo.com", nome="Perfil", foto_url=FOTO)
    cabecalho = {"Authorization": f"Bearer {criar_access_token(vendedor.id)}"}
    resposta = cliente_http.get("/auth/me", headers=cabecalho)
    assert resposta.status_code == 200
    assert resposta.json()["foto_url"] == FOTO
