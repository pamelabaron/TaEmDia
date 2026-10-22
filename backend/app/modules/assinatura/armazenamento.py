"""Guarda os comprovantes enviados.

Três cuidados que valem a pena explicar:

1. O nome do arquivo salvo é gerado pelo sistema (UUID). O nome digitado pelo
   usuário **nunca** entra na formação do caminho. É assim que se evita que
   alguém envie "../../etc/algo" e escreva fora da pasta.
2. O tipo é validado pelos **primeiros bytes** do arquivo, não pela extensão.
   Renomear "virus.exe" para "comprovante.png" não engana a assinatura binária.
3. A pasta fica fora de qualquer diretório servido como estático: o arquivo só
   sai por endpoint autenticado de administradora.
"""
import uuid
from pathlib import Path

from app.core.config import settings

#: Tipos aceitos e a assinatura binária que cada um precisa ter no início.
ASSINATURAS = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "application/pdf": (b"%PDF-",),
}

#: 5 MB.
TAMANHO_MAXIMO = 5 * 1024 * 1024

EXTENSOES = {"image/jpeg": ".jpg", "image/png": ".png", "application/pdf": ".pdf"}


class ArquivoInvalido(Exception):
    """O arquivo enviado não é um comprovante aceitável."""


def detectar_tipo(conteudo: bytes) -> str:
    """Descobre o tipo pelo conteúdo. Levanta ArquivoInvalido se não reconhecer."""
    for tipo, inicios in ASSINATURAS.items():
        if any(conteudo.startswith(i) for i in inicios):
            return tipo
    raise ArquivoInvalido("Envie uma imagem (JPG ou PNG) ou um PDF.")


def validar(conteudo: bytes) -> str:
    if not conteudo:
        raise ArquivoInvalido("O arquivo está vazio.")
    if len(conteudo) > TAMANHO_MAXIMO:
        raise ArquivoInvalido("O arquivo passa de 5 MB.")
    return detectar_tipo(conteudo)


def guardar(conteudo: bytes, tipo: str) -> str:
    """Salva com nome gerado pelo sistema e devolve o caminho."""
    pasta = Path(settings.UPLOADS_DIR)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{uuid.uuid4()}{EXTENSOES[tipo]}"
    destino.write_bytes(conteudo)
    return str(destino)
