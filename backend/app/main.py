"""Ponto de entrada da API TáEmDia."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.modules.auth.router import router as auth_router
from app.modules.clientes.router import router as clientes_router
from app.modules.vendas.router import router as vendas_router
from app.modules.relatorios.router import router as relatorios_router
from app.modules.templates.router import router as templates_router
from app.modules.configuracoes.router import router as configuracoes_router
from app.modules.cobrancas.router import router as cobrancas_router
from app.modules.assinatura.router import router as assinatura_router

from app.core.config import settings
from app.modules.agente.agendador import iniciar_agendador, parar_agendador


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Valida a configuração, liga o agendador ao subir a API e desliga ao encerrar."""
    if settings.em_producao:
        problemas = settings.validar_para_producao()
        if problemas:
            raise RuntimeError(
                "Configuração insegura para produção: " + "; ".join(problemas)
            )
    if settings.AGENDADOR_ATIVO:
        iniciar_agendador()
    yield
    parar_agendador()


app = FastAPI(
    title="TáEmDia API",
    description="Cobrança automatizada via WhatsApp e gestão de carteira de clientes.",
    version="0.1.0",
    lifespan=ciclo_de_vida,
)

# Libera o frontend Angular (localhost:4200) a chamar a API durante o desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origens_permitidas,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["infra"])
def health_check(db: Session = Depends(get_db)):
    """Verifica se a API está no ar **e** se o banco responde.

    É o endereço que o monitor (.github/workflows/monitor.yml) consulta. Antes
    ele respondia "ok" sem olhar o banco: com o PostgreSQL parado, a API
    continuava jurando que estava tudo bem, e o monitor ficaria verde com o
    sistema quebrado.

    Fala com o banco direto, sem repository, de propósito: não lê dado de
    ninguém, só pergunta se a conexão existe. Por isso também não exige login.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "fora do ar", "servico": "taemdia-api", "banco": "sem resposta"},
        )
    return {"status": "ok", "servico": "taemdia-api", "banco": "ok"}


# Módulos do domínio (crescem sprint a sprint)
app.include_router(auth_router)
app.include_router(clientes_router)
app.include_router(vendas_router)
app.include_router(relatorios_router)
app.include_router(templates_router)
app.include_router(configuracoes_router)
app.include_router(cobrancas_router)
app.include_router(assinatura_router)
