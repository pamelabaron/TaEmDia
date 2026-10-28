"""A Política de Privacidade e os Termos precisam existir e ser alcançáveis.

Exigência da LGPD, e não detalhe de forma: o sistema guarda nome, CPF e
telefone de **terceiros**, pessoas que devem ao vendedor e que nunca entraram
no site. Elas têm direito de saber que estão ali e de pedir para sair.

Três coisas que este arquivo protege, e que são fáceis de quebrar sem perceber:

1. **As páginas atrás de login.** Política de privacidade que só quem tem conta
   consegue ler não cumpre a função: justamente quem não tem conta é quem
   precisa dela. Basta alguém acrescentar o `authGuard` por hábito.
2. **O link sumir do rodapé.** Documento publicado que ninguém acha é o mesmo
   que documento inexistente.
3. **O contato ficar com texto de exemplo.** Prometer um canal que não existe
   é pior do que não prometer nada.
"""
import re

import pytest

from .caminhos import achar

ROTAS = achar("frontend", "src", "app", "app.routes.ts")
ENTRADA = achar("frontend", "src", "app", "pages", "login", "login.component.ts")
PRIVACIDADE = achar("frontend", "src", "app", "pages", "legal", "privacidade.component.ts")
TERMOS = achar("frontend", "src", "app", "pages", "legal", "termos.component.ts")

#: Os dois documentos e o endereço de cada um.
PAGINAS = [("privacidade", "Política de Privacidade"), ("termos", "Termos de Uso")]


@pytest.fixture(scope="module")
def rotas() -> str:
    if ROTAS is None:
        pytest.skip("app.routes.ts não encontrado")
    return ROTAS.read_text(encoding="utf-8")


def _bloco_da_rota(texto: str, caminho: str) -> str | None:
    """O trecho de configuração de uma rota, do nome dela até o fecho."""
    achado = re.search(
        r"\{\s*path:\s*'" + re.escape(caminho) + r"'.*?\n  \}",
        texto,
        re.S,
    )
    return achado.group(0) if achado else None


@pytest.mark.parametrize("caminho, nome", PAGINAS)
def test_a_pagina_existe(caminho, nome):
    arquivo = PRIVACIDADE if caminho == "privacidade" else TERMOS
    assert arquivo is not None, f"Falta a página de {nome}."
    assert arquivo.read_text(encoding="utf-8").strip(), f"A página de {nome} está vazia."


@pytest.mark.parametrize("caminho, nome", PAGINAS)
def test_a_rota_existe(rotas, caminho, nome):
    assert _bloco_da_rota(rotas, caminho) is not None, (
        f"Não há rota /{caminho} em app.routes.ts, então a página de {nome} "
        "não é alcançável por endereço nenhum."
    )


@pytest.mark.parametrize("caminho, nome", PAGINAS)
def test_a_pagina_abre_sem_login(rotas, caminho, nome):
    bloco = _bloco_da_rota(rotas, caminho)
    if bloco is None:
        pytest.skip("a rota não existe; o teste anterior cobre isso")

    assert "authGuard" not in bloco, (
        f"A rota /{caminho} exige login. Quem precisa ler {nome} é justamente "
        "quem ainda não tem conta."
    )
    assert "visitanteGuard" not in bloco, (
        f"A rota /{caminho} empurra quem já entrou para outro lugar. "
        "Quem tem conta também tem direito de reler o documento."
    )


def test_o_rodape_leva_aos_dois_documentos():
    if ENTRADA is None:
        pytest.skip("página de entrada não encontrada")

    texto = ENTRADA.read_text(encoding="utf-8")
    rodape = re.search(r'<footer class="rodape">.*?</footer>', texto, re.S)
    assert rodape, "Não achei o rodapé da página de entrada"

    faltando = [
        caminho for caminho, _ in PAGINAS
        if f'"/{caminho}"' not in rodape.group(0) and f"'/{caminho}'" not in rodape.group(0)
    ]
    assert not faltando, (
        f"O rodapé não leva a: {faltando}. Documento que ninguém acha é o "
        "mesmo que documento inexistente."
    )


#: Marcas de texto por preencher que não podem sobrar num documento publicado.
#: Cada uma vem com a informação de respeitar ou não a caixa das letras:
#: "TODO" em maiúsculas é marca de código, mas "todo" é palavra comum em
#: português ("todo o acesso acontece por conexão cifrada") e a primeira
#: versão deste teste reprovou os dois documentos por causa dela.
DE_EXEMPLO = [
    ("seu-email", False),
    ("exemplo@", False),
    ("preencher aqui", False),
    ("TODO", True),
    ("XXXX", True),
    ("FIXME", True),
]


@pytest.mark.parametrize("caminho, nome", PAGINAS)
def test_o_contato_nao_e_texto_de_exemplo(caminho, nome):
    arquivo = PRIVACIDADE if caminho == "privacidade" else TERMOS
    if arquivo is None:
        pytest.skip("a página não existe; outro teste cobre isso")

    texto = arquivo.read_text(encoding="utf-8")

    sobrou = [
        marca for marca, sensivel in DE_EXEMPLO
        if (marca in texto if sensivel else marca.lower() in texto.lower())
    ]
    assert not sobrou, (
        f"A página de {nome} ainda tem texto de exemplo: {sobrou}. "
        "Prometer um canal de contato que não existe é pior que não prometer."
    )

    # O arroba aparece como "&#64;" no código: solto no template do Angular 17
    # ele colide com a sintaxe de blocos (@if, @for). No navegador o endereço
    # sai normal, então a conferência desfaz o código antes de procurar.
    legivel = texto.replace("&#64;", "@")

    assert re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", legivel), (
        f"A página de {nome} não traz endereço de contato. A LGPD exige um "
        "canal para a pessoa pedir seus dados ou a exclusão deles."
    )
