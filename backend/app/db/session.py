"""Conexão com o banco (engine) e sessão do SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base da qual todos os modelos (tabelas) herdam.
Base = declarative_base()


def get_db():
    """Fornece uma sessão de banco por requisição (usado via Depends do FastAPI)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
