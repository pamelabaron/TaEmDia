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
import re
import uuid
from pathlib import PurePosixPath, PureWindowsPath, Path

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


#: Limite do nome original guardado no banco. Não é regra de negócio: é o
#: tamanho acima do qual o nome deixa de informar e vira despejo de texto.
NOME_MAXIMO = 120

#: Usado quando não sobra nome nenhum. A coluna é obrigatória no banco.
NOME_PADRAO = "comprovante"

#: Caracteres de controle: quebra de linha, tabulação, nulo e companhia.
_CONTROLE = re.compile(r"[\x00-\x1f\x7f]")


class ArquivoInvalido(Exception):
    """O arquivo enviado não é um comprovante aceitável."""


def nome_seguro(nome: str | None) -> str:
    """Limpa o nome que veio do cliente HTTP, para guardar e exibir.

    Este nome **não** forma o caminho em disco: o arquivo salvo tem nome
    gerado aqui (ver `guardar`). Ele existe só para a administradora ver
    "nota-de-outubro.pdf" em vez de um UUID, e vai para o cabeçalho
    `Content-Disposition` no download.

    Mesmo assim ele é limpo, por três motivos somados: é texto de fora, não
    tem limite de tamanho na coluna, e é mais barato tratar agora do que
    depois que houver dado de verdade para migrar.

    Três passos: tirar o caminho, tirar caractere de controle, e cortar no
    tamanho preservando a extensão.
    """
    bruto = (nome or "").strip()
    # Os dois sabores de separador, porque quem envia pode estar no Windows e
    # o PurePosixPath sozinho não reconheceria a contrabarra.
    so_nome = PureWindowsPath(PurePosixPath(bruto).name).name
    limpo = _CONTROLE.sub("", so_nome).strip().strip(".")
    if not limpo:
        return NOME_PADRAO
    if len(limpo) <= NOME_MAXIMO:
        return limpo

    # Corta o miolo, não o fim: a extensão é o que diz o que será aberto.
    extensao = Path(limpo).suffix[:16]
    return limpo[: NOME_MAXIMO - len(extensao)] + extensao


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
