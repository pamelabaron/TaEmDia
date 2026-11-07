"""Relógio do sistema em UTC.

As colunas de data e hora do banco guardam UTC sem fuso. Antes elas usavam a
chamada de UTC do datetime que foi descontinuada no Python 3.12 (apontamento
da revisão de código da N1). Esta função devolve o mesmo valor pelo caminho
recomendado.

Para "que dia é hoje" use hoje_brasilia(), em cobrancas/regras.py: o dia do
sistema é o de Brasília (RN11).
"""
from datetime import datetime, timezone


def agora_utc() -> datetime:
    """Agora em UTC, sem fuso, no formato que as colunas do banco guardam."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
