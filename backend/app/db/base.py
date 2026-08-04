"""Reúne a Base e importa todos os modelos, para o Alembic detectar as tabelas.
Sempre que criar um modelo novo, importe-o aqui."""
from app.db.session import Base  # noqa: F401

# Importa os modelos para que fiquem registrados em Base.metadata.
from app.modules.vendedores.models import Vendedor, Configuracao  # noqa: F401
from app.modules.clientes.models import Cliente  # noqa: F401
from app.modules.vendas.models import Venda, Parcela  # noqa: F401
