"""Ponto de entrada da API TáEmDia."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.router import router as auth_router
from app.modules.clientes.router import router as clientes_router
from app.modules.vendas.router import router as vendas_router
from app.modules.relatorios.router import router as relatorios_router

app = FastAPI(
    title="TáEmDia API",
    description="Cobrança automatizada via WhatsApp e gestão de carteira de clientes.",
    version="0.1.0",
)

# Libera o frontend Angular (localhost:4200) a chamar a API durante o desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["infra"])
def health_check():
    """Verifica se a API está no ar."""
    return {"status": "ok", "servico": "taemdia-api"}


# Módulos do domínio (crescem sprint a sprint)
app.include_router(auth_router)
app.include_router(clientes_router)
app.include_router(vendas_router)
app.include_router(relatorios_router)
