"""Configuração compartilhada dos testes.

Usa um banco PostgreSQL separado (`taemdia_test`) para não tocar nos dados reais.
As tabelas são criadas uma vez e limpas antes de cada teste.
"""
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Aponta para o banco de testes antes de importar a configuração da aplicação.
URL_BASE = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://taemdia:troque_esta_senha@db:5432/taemdia"
)
URL_TESTE = URL_BASE.rsplit("/", 1)[0] + "/taemdia_test"
os.environ["DATABASE_URL"] = URL_TESTE
# O agendador não deve rodar durante os testes.
os.environ["AGENDADOR_ATIVO"] = "false"

from app.db.base import Base  # noqa: E402  (import após ajustar a variável)
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


def _garantir_banco_de_teste() -> None:
    """Cria o banco de testes, se ainda não existir."""
    admin = create_engine(URL_BASE.rsplit("/", 1)[0] + "/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        existe = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'taemdia_test'")
        ).scalar()
        if not existe:
            conn.execute(text("CREATE DATABASE taemdia_test"))
    admin.dispose()


@pytest.fixture(scope="session")
def engine():
    _garantir_banco_de_teste()
    eng = create_engine(URL_TESTE)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture(autouse=True)
def uploads_isolados(tmp_path, monkeypatch):
    """Comprovantes enviados nos testes vão para uma pasta temporária.

    Mesmo motivo do banco separado: teste não toca em dado real. Sem isto,
    cada rodada da suíte deixava arquivos órfãos na pasta de comprovantes.
    """
    from app.core.config import settings

    monkeypatch.setattr(settings, "UPLOADS_DIR", str(tmp_path / "uploads"))


@pytest.fixture()
def db(engine):
    """Sessão limpa para cada teste."""
    tabelas = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))
    Session = sessionmaker(bind=engine)
    sessao = Session()
    try:
        yield sessao
    finally:
        sessao.close()


@pytest.fixture()
def cliente_http(db):
    """Cliente HTTP de teste, ligado à mesma sessão de banco do teste."""
    from fastapi.testclient import TestClient

    def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _criar_vendedor(db, email: str, nome: str, dias_de_acesso: int | None, origem: str = "teste"):
    """Cria um vendedor e, quando pedido, a vigência da assinatura dele.

    `dias_de_acesso=None` cria um vendedor sem nenhuma assinatura. O estado de
    quem já venceu e nunca pagou.
    """
    from datetime import date, timedelta

    from app.modules.assinatura.models import Assinatura
    from app.modules.vendedores.models import Vendedor

    v = Vendedor(google_email=email, nome=nome, whatsapp_numero="5547900000000")
    db.add(v)
    db.commit()
    db.refresh(v)
    if dias_de_acesso is not None:
        db.add(Assinatura(vendedor_id=v.id,
                          valido_ate=date.today() + timedelta(days=dias_de_acesso),
                          origem=origem))
        db.commit()
    return v


@pytest.fixture()
def vendedor(db):
    """Vendedor com acesso liberado. É o estado de quem acabou de se cadastrar
    (o login cria 7 dias de teste, RN-A01)."""
    return _criar_vendedor(db, "teste@exemplo.com", "Vendedor Teste", dias_de_acesso=7)


@pytest.fixture()
def vendedor_vencido(db):
    """Vendedor cuja assinatura venceu ontem."""
    return _criar_vendedor(db, "vencido@exemplo.com", "Vendedor Vencido",
                           dias_de_acesso=-1, origem="pago")


@pytest.fixture()
def cabecalho_vencido(vendedor_vencido):
    from app.core.security import criar_access_token

    return {"Authorization": f"Bearer {criar_access_token(vendedor_vencido.id)}"}


@pytest.fixture()
def cabecalho_auth(vendedor):
    """Cabeçalho Authorization com um JWT válido do vendedor de teste."""
    from app.core.security import criar_access_token

    return {"Authorization": f"Bearer {criar_access_token(vendedor.id)}"}
