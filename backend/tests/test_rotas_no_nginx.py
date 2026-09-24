"""As telas do site e os endereços da API não podem colidir no Nginx.

Em produção o Nginx é a porta de entrada e decide, pelo caminho, o que vai para
a API e o que vai para o site. Como o site é uma aplicação de página única, o
navegador só pede um caminho ao servidor quando a pessoa digita o endereço,
atualiza a página ou abre um link salvo. Se esse caminho cair na API, ela
recebe JSON no lugar do sistema.

Foi o que aconteceu com /auth/callback, a tela que recebe o retorno do Google:
o Nginx mandava todo /auth para a API, e o login terminava em "Not Found".
As telas /clientes, /cobrancas, /configuracoes e /assinaturas tinham o mesmo
defeito, à espera de alguém atualizar a página.

A separação adotada: a API vive sob /api, e o login do Google continua na raiz,
porque o endereço de retorno já está cadastrado no Google Cloud e mudá-lo
exigiria reconfigurar lá fora.
"""
import re
from pathlib import Path

import pytest
from fastapi.routing import APIRoute

from app.main import app

#: Único trecho da raiz que pertence à API. O Google redireciona para cá.
RAIZ_DA_API = "/auth/google"


def _achar(*partes: str) -> Path | None:
    for pasta in Path(__file__).resolve().parents:
        candidato = pasta.joinpath(*partes)
        if candidato.is_file():
            return candidato
    return None


CONF = _achar("docker", "nginx", "taemdia.conf")
ROTAS_ANGULAR = _achar("frontend", "src", "app", "app.routes.ts")


@pytest.fixture(scope="module")
def conf() -> str:
    if CONF is None:
        pytest.skip("taemdia.conf não encontrado")
    return CONF.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def caminhos_do_site() -> list[str]:
    if ROTAS_ANGULAR is None:
        pytest.skip("app.routes.ts não encontrado")
    texto = ROTAS_ANGULAR.read_text(encoding="utf-8")
    caminhos = []
    for achado in re.findall(r"path:\s*'([^']*)'", texto):
        if achado in ("", "**"):
            continue
        # :id vira um valor qualquer, para o teste comparar um caminho real.
        caminhos.append("/" + re.sub(r":\w+", "abc123", achado))
    return caminhos


def test_a_api_fica_sob_api(conf):
    """Existe um location /api/ encaminhando para o backend."""
    assert re.search(r"location\s+/api/\s*\{[^}]*proxy_pass\s+http://backend:8000", conf, re.S), (
        "o Nginx precisa de um location /api/ apontando para o backend"
    )


def test_o_login_do_google_continua_na_raiz(conf):
    assert re.search(rf"location[^\n]*{re.escape(RAIZ_DA_API)}", conf), (
        "o retorno do Google está cadastrado na raiz e precisa continuar chegando à API"
    )


def test_nenhuma_tela_do_site_cai_na_api(conf, caminhos_do_site):
    """Nenhum caminho de tela pode bater com um trecho da raiz mandado à API."""
    raizes = re.findall(r"location\s+~\s+\^(/[\w/|()\.-]+)", conf)
    problemas = []
    for caminho in caminhos_do_site:
        for raiz in raizes:
            if re.match(raiz, caminho):
                problemas.append(f"{caminho} cairia em {raiz}")
    assert not problemas, (
        "Telas do site que o Nginx entregaria à API (a pessoa veria JSON ao "
        "atualizar a página): " + "; ".join(problemas)
    )


def test_toda_rota_da_api_e_alcancavel(conf):
    """Cada rota registrada precisa chegar ao backend por /api ou pela raiz permitida."""
    inalcancaveis = []
    for rota in app.routes:
        if not isinstance(rota, APIRoute):
            continue
        if rota.path.startswith(RAIZ_DA_API):
            continue          # chega pela exceção do Google
        if rota.path.startswith("/"):
            continue          # chega por /api + o mesmo caminho
        inalcancaveis.append(rota.path)
    assert not inalcancaveis, inalcancaveis
