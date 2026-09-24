"""Toda rota da API precisa estar na lista do Nginx.

Em produção o Nginx é a porta de entrada: ele decide o que vai para a API e o
que vai para a interface. A decisão é uma lista de prefixos escrita à mão. Rota
nova que não entra nessa lista não chega ao backend. O visitante recebe a
página do Angular no lugar da resposta, e o erro só aparece depois de publicar.

Foi o que aconteceu com /assinatura e /admin: existiam no código, funcionavam no
computador de desenvolvimento e sumiam no servidor.
"""
import re
from pathlib import Path

import pytest
from fastapi.routing import APIRoute

from app.main import app


def _achar_conf() -> Path | None:
    for pasta in Path(__file__).resolve().parents:
        candidato = pasta / "docker" / "nginx" / "taemdia.conf"
        if candidato.is_file():
            return candidato
    return None


CONF = _achar_conf()


@pytest.fixture(scope="module")
def prefixos_do_nginx() -> set[str]:
    if CONF is None:
        pytest.skip("taemdia.conf não encontrado")
    texto = CONF.read_text(encoding="utf-8")
    achado = re.search(r"location\s+~\s+\^/\(([^)]+)\)", texto)
    assert achado, "não encontrei a lista de rotas da API no Nginx"
    return {p.strip() for p in achado.group(1).split("|")}


def _prefixos_da_api() -> set[str]:
    """Primeiro pedaço do caminho de cada rota registrada."""
    prefixos = set()
    for rota in app.routes:
        if not isinstance(rota, APIRoute):
            continue
        partes = rota.path.strip("/").split("/")
        if partes and partes[0]:
            prefixos.add(partes[0])
    return prefixos


def test_encontrou_rotas_para_comparar():
    assert len(_prefixos_da_api()) >= 8


def test_toda_rota_da_api_passa_pelo_nginx(prefixos_do_nginx):
    faltando = sorted(p for p in _prefixos_da_api() if p not in prefixos_do_nginx)
    assert not faltando, (
        "Rotas da API que o Nginx não encaminha (o visitante receberia a página "
        "do Angular no lugar da resposta): " + ", ".join(faltando)
        + ". Acrescente à lista em docker/nginx/taemdia.conf."
    )
