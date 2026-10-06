"""A Wiki do GitHub é gerada a partir da pasta docs/, nunca editada na mão.

O playbook do portfólio exige documentação na Wiki do repositório. Manter as
duas na mão criaria duas versões do mesmo texto, e uma delas envelheceria sem
ninguém notar. Aqui a pasta docs/ é o original e a Wiki é a cópia publicada.

Estes testes protegem a cópia de três descuidos:

1. documento novo em docs/ que ninguém batizou, e chegaria na Wiki com um nome
   feio derivado do arquivo;
2. nome de página com acento, que vira endereço codificado e feio;
3. link entre documentos que funciona no repositório e quebra na Wiki, porque
   lá não existe a pasta docs/.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from .caminhos import achar, achar_pasta


GERADOR = achar("scripts", "wiki.py")
DOCS = achar_pasta("docs")


def _carregar_gerador():
    if GERADOR is None:
        pytest.skip("scripts/wiki.py não encontrado")
    spec = importlib.util.spec_from_file_location("wiki", GERADOR)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["wiki"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def wiki():
    return _carregar_gerador()


@pytest.fixture(scope="module")
def raiz() -> Path:
    if GERADOR is None:
        pytest.skip("repositório não encontrado")
    return GERADOR.parent.parent


def test_todo_documento_de_docs_tem_titulo_proprio(wiki, raiz):
    """Documento novo sem título batizado entraria na Wiki com nome feio.

    O gerador tem uma saída de emergência que deriva o nome do arquivo, para
    nunca deixar um documento de fora. Este teste garante que a saída de
    emergência continue sendo emergência, e não o caminho normal.
    """
    if DOCS is None:
        pytest.skip("pasta docs/ não encontrada")

    sem_titulo = []
    for arquivo in sorted(DOCS.glob("*.md")):
        relativo = f"docs/{arquivo.name}"
        if relativo not in wiki.TITULOS:
            sem_titulo.append(relativo)

    assert not sem_titulo, (
        "Documentos sem título para a Wiki: "
        + ", ".join(sem_titulo)
        + ". Acrescente cada um ao dicionário TITULOS em scripts/wiki.py."
    )


def test_nome_do_arquivo_nao_leva_acento(wiki):
    """Acento no nome do arquivo vira endereço codificado (Deploy%20em%20produ...)."""
    assert wiki.arquivo_da_pagina("Deploy em produção") == "Deploy-em-producao"
    assert wiki.arquivo_da_pagina("Checklist de segurança") == "Checklist-de-seguranca"
    assert wiki.arquivo_da_pagina("Testes") == "Testes"


def test_link_entre_documentos_vira_link_da_wiki(wiki):
    """Na Wiki não existe a pasta docs/, então o caminho relativo quebraria."""
    texto = "Detalhes em [testes](docs/testes.md) e em [rodar](COMO-RODAR.md)."
    esperado = "Detalhes em [testes](Testes) e em [rodar](Como-rodar-o-projeto)."
    assert wiki.reescrever_links(texto) == esperado


def test_link_para_fora_nao_e_tocado(wiki):
    """Link externo e âncora dentro da própria página seguem como estão."""
    texto = "Veja o [site](https://taemdia.duckdns.org) e a [seção](#testes)."
    assert wiki.reescrever_links(texto) == texto


def test_gerar_escreve_todas_as_paginas(wiki, raiz, tmp_path):
    """A Wiki completa: índice, menu lateral e uma página por documento."""
    paginas = wiki.gerar(raiz, tmp_path)

    assert (tmp_path / "Home.md").is_file()
    assert (tmp_path / "_Sidebar.md").is_file()

    for titulo, arquivo in paginas.items():
        destino = tmp_path / f"{arquivo}.md"
        assert destino.is_file(), f"Página '{titulo}' não foi escrita"
        assert destino.read_text(encoding="utf-8").strip(), f"Página '{titulo}' vazia"


def test_menu_lateral_aponta_para_paginas_que_existem(wiki, raiz, tmp_path):
    """Menu com link quebrado é pior que menu nenhum: o leitor se perde."""
    wiki.gerar(raiz, tmp_path)

    menu = (tmp_path / "_Sidebar.md").read_text(encoding="utf-8")
    alvos = wiki.links_do_texto(menu)

    assert alvos, "O menu lateral não tem nenhum link"
    for alvo in alvos:
        assert (tmp_path / f"{alvo}.md").is_file(), (
            f"O menu aponta para '{alvo}', que não foi gerada"
        )


def test_nenhuma_pagina_mantem_link_para_a_pasta_docs(wiki, raiz, tmp_path):
    """Sobrou um caminho de repositório no texto publicado."""
    wiki.gerar(raiz, tmp_path)

    com_sobra = [
        pagina.name
        for pagina in tmp_path.glob("*.md")
        if "](docs/" in pagina.read_text(encoding="utf-8")
    ]
    assert not com_sobra, f"Páginas com link para docs/: {com_sobra}"
