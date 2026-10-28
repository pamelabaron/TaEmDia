"""O ícone e o título da aba são a primeira coisa que aparece do produto.

Numa aba de 16 pixels não cabe nome, só a marca. Se o ícone ficar com a cor
do tema antigo, o produto se apresenta com duas identidades: uma na aba e
outra na tela.

Aconteceu: o ícone nasceu petróleo com o visto em lima, cores do tema verde,
e continuou assim depois de o sistema inteiro virar ameixa.
"""
import re
import xml.etree.ElementTree as ET

import pytest

from .caminhos import achar

ICONE = achar("frontend", "src", "icone.svg")
PAGINA = achar("frontend", "src", "index.html")

#: Cores do tema antigo que não podem mais aparecer no ícone.
TEMA_ANTIGO = {
    "#0a4239": "petróleo",
    "#04231f": "petróleo escuro",
    "#c3f25e": "lima",
    "#3cb676": "verde",
    "#1f824d": "verde escuro",
}

#: Cores do tema atual, as únicas que o ícone pode usar.
TEMA_ATUAL = {"#3f2a59", "#0f0b14", "#ddc7ff"}


@pytest.fixture(scope="module")
def icone() -> str:
    if ICONE is None:
        pytest.skip("icone.svg não encontrado")
    return ICONE.read_text(encoding="utf-8")


def test_o_icone_e_xml_valido(icone):
    """Comentário com dois hifens seguidos quebra o XML, e o ícone deixa de
    ser lido por qualquer ferramenta que gere o .ico e o do iPhone a partir
    dele. Foi assim que a primeira geração falhou: o comentário citava os
    nomes dos tokens (que começam com dois hifens)."""
    try:
        ET.fromstring(icone)
    except ET.ParseError as erro:
        pytest.fail(f"icone.svg não é XML válido: {erro}")


def test_o_icone_nao_usa_as_cores_do_tema_antigo(icone):
    sobrou = [
        f"{cor} ({nome})" for cor, nome in TEMA_ANTIGO.items()
        if cor.lower() in icone.lower()
    ]
    assert not sobrou, (
        "O ícone ainda usa cores do tema antigo: " + ", ".join(sobrou)
        + ". A aba mostraria uma marca e a tela, outra."
    )


def test_o_icone_usa_a_paleta_atual(icone):
    usadas = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}", icone)}
    fora = usadas - {c.lower() for c in TEMA_ATUAL}
    assert not fora, (
        f"O ícone usa cores que não são da paleta: {sorted(fora)}. "
        f"As permitidas são {sorted(TEMA_ATUAL)}."
    )


def test_os_tres_arquivos_do_icone_existem():
    """O navegador escolhe entre eles conforme o caso: o SVG na aba moderna,
    o .ico no histórico e nos antigos, o PNG quando se salva na tela inicial
    do iPhone. Faltando um, a marca some naquele lugar."""
    faltando = [
        nome for nome in ("icone.svg", "favicon.ico", "apple-touch-icon.png")
        if achar("frontend", "src", nome) is None
    ]
    assert not faltando, f"Arquivos de ícone que faltam: {faltando}"


def test_o_titulo_da_aba_e_so_o_nome():
    """Nome com descrição junto é cortado pela metade na aba, e o que sobra
    costuma ser o pedaço que menos identifica."""
    if PAGINA is None:
        pytest.skip("index.html não encontrado")

    achado = re.search(r"<title>(.*?)</title>", PAGINA.read_text(encoding="utf-8"))
    assert achado, "A página não tem título"

    titulo = achado.group(1).strip()
    assert titulo == "TáEmDia", (
        f'O título da aba é "{titulo}". Deve ser apenas "TáEmDia".'
    )
