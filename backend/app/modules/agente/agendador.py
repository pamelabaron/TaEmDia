"""Agendador de tarefas em segundo plano (APScheduler) — RFC 5.3.5.

Dois jobs:
  (a) varredura de parcelas para envio automático, de hora em hora dentro do
      horário comercial;
  (b) envio do resumo analítico diário, no horário configurado por cada vendedor.
"""
import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import SessionLocal
from app.modules.agente.service import AgenteService
from app.modules.cobrancas.regras import agora_brasilia, dentro_horario_comercial
from app.modules.cobrancas.repository import (
    CobrancaLogRepository,
    CobrancaParcelaRepository,
    RespostaRepository,
)
from app.modules.cobrancas.service import CobrancaService
from app.modules.configuracoes.repository import ConfiguracaoRepository
from app.modules.configuracoes.service import ConfiguracaoService
from app.modules.templates.repository import TemplateRepository
from app.modules.vendedores.models import Vendedor
from app.modules.whatsapp.client import get_whatsapp_client

logger = logging.getLogger(__name__)


def _vendedores_ativos(db):
    return db.query(Vendedor).filter(Vendedor.ativo.is_(True)).all()


def job_varredura_cobrancas() -> None:
    """Varre as parcelas e envia as cobranças automáticas de cada vendedor."""
    if not dentro_horario_comercial():
        return
    db = SessionLocal()
    try:
        servico = CobrancaService(
            CobrancaLogRepository(db), CobrancaParcelaRepository(db),
            TemplateRepository(db), get_whatsapp_client(),
        )
        config_service = ConfiguracaoService(ConfiguracaoRepository(db))
        for vendedor in _vendedores_ativos(db):
            config = config_service.obter(vendedor.id)
            if not config.envio_auto_global:
                continue
            enviados = servico.varrer_e_cobrar(
                vendedor.id, config.dias_antecedencia_lembrete
            )
            if enviados:
                logger.info("Varredura: %s cobranças enviadas para %s", len(enviados), vendedor.google_email)
    except Exception:  # o agendador nunca deve derrubar a aplicação
        logger.exception("Falha na varredura de cobranças")
    finally:
        db.close()


def job_resumo_diario() -> None:
    """Envia o resumo do dia aos vendedores cujo horário configurado chegou."""
    agora = agora_brasilia()
    db = SessionLocal()
    try:
        agente = AgenteService(
            CobrancaParcelaRepository(db), RespostaRepository(db),
            CobrancaLogRepository(db), get_whatsapp_client(),
        )
        config_service = ConfiguracaoService(ConfiguracaoRepository(db))
        for vendedor in _vendedores_ativos(db):
            config = config_service.obter(vendedor.id)
            if not config.resumo_ativo or not vendedor.whatsapp_numero:
                continue
            # Envia quando a hora e o minuto configurados chegam (job roda a cada 15 min).
            if config.horario_resumo.hour != agora.hour:
                continue
            if abs(config.horario_resumo.minute - agora.minute) > 7:
                continue
            enviado = agente.enviar_resumo(vendedor.id, vendedor.whatsapp_numero, date.today())
            if enviado:
                logger.info("Resumo diário enviado para %s", vendedor.google_email)
    except Exception:
        logger.exception("Falha no envio do resumo diário")
    finally:
        db.close()


_scheduler: BackgroundScheduler | None = None


def iniciar_agendador() -> BackgroundScheduler:
    """Liga o agendador (chamado no startup da API)."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    sched = BackgroundScheduler(timezone="America/Sao_Paulo")
    # (a) varredura de hora em hora, no minuto 5, das 08h às 20h.
    sched.add_job(
        job_varredura_cobrancas, CronTrigger(hour="8-20", minute=5),
        id="varredura_cobrancas", replace_existing=True,
    )
    # (b) resumo diário: verifica a cada 15 minutos quem já atingiu o horário.
    sched.add_job(
        job_resumo_diario, CronTrigger(minute="0,15,30,45"),
        id="resumo_diario", replace_existing=True,
    )
    sched.start()
    _scheduler = sched
    logger.info("Agendador iniciado (varredura horária + resumo diário).")
    return sched


def parar_agendador() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
