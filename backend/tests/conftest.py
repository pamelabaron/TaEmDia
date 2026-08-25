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


@pytest.fixture()
def vendedor(db):
    """Um vendedor pronto para uso nos testes."""
    from app.modules.vendedores.models import Vendedor

    v = Vendedor(google_email="teste@exemplo.com", nome="Vendedor Teste",
                 whatsapp_numero="5547900000000")
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@pytest.fixture()
def cabecalho_auth(vendedor):
    """Cabeçalho Authorization com um JWT válido do vendedor de teste."""
    from app.core.security import criar_access_token

    return {"Authorization": f"Bearer {criar_access_token(vendedor.id)}"}
