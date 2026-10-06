"""Autenticação do webhook do WhatsApp.

O webhook é chamado pelo serviço de WhatsApp (Evolution API), não pelo navegador,
por isso não usa JWT. A proteção é um segredo compartilhado: sem ele, qualquer um
poderia forjar respostas de devedores.
"""
import hmac

from fastapi import Header, HTTPException, Query, status

from app.core.config import settings


def validar_token_webhook(
    x_webhook_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> None:
    """Aceita o segredo pelo cabeçalho `X-Webhook-Token` ou pelo parâmetro `token`
    (a Evolution API permite configurar a URL, mas nem sempre cabeçalhos).

    Quando `WEBHOOK_TOKEN` não está configurado, o sistema está em modo de
    desenvolvimento/simulador e a verificação é dispensada.
    """
    esperado = settings.WEBHOOK_TOKEN
    if not esperado:
        if settings.em_producao:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook desabilitado: WEBHOOK_TOKEN não configurado.",
            )
        return

    recebido = x_webhook_token or token or ""
    # Comparação em tempo constante, para não vazar o segredo por tempo de resposta.
    if not hmac.compare_digest(recebido, esperado):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token do webhook inválido.",
        )
