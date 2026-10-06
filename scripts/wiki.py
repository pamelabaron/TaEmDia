"""Gera a Wiki do GitHub a partir da documentação do repositório.

O playbook do portfólio exige documentação na Wiki. Manter a Wiki e a pasta
docs/ na mão criaria duas versões do mesmo texto, e uma envelheceria sem
ninguém notar. Aqui a pasta docs/ é o original e a Wiki é a cópia publicada:
ninguém edita a Wiki, ela é reescrita a cada envio para o repositório.

Uso:

    python scripts/wiki.py <pasta-de-saida>

O robô em .github/workflows/wiki.yml chama este script e envia o resultado.
Os testes vivem em backend/tests/test_wiki.py.
"""
import re
import sys
import unicodedata
from pathlib import Path

#: Como cada documento se chama na Wiki. O caminho é relativo à raiz do
#: repositório. Documento fora desta lista ainda é publicado, com um nome
#: derivado do arquivo, mas o teste reclama: nome bom se escolhe, não se deduz.
TITULOS = {
    "COMO-RODAR.md": "Como rodar o projeto",
    "docs/instalacao-ambiente.md": "Instalação do ambiente",
    "docs/modelo-de-dados.md": "Modelo de dados",
    "docs/testes.md": "Testes",
    "docs/deploy.md": "Deploy em produção",
    "docs/checklist-seguranca.md": "Checklist de segurança",
    "docs/whatsapp-conectar.md": "Conectar o WhatsApp",
    "docs/google-oauth-setup.md": "Login com o Google",
}

#: A ordem do menu lateral. Do primeiro contato ao que só interessa depois.
ORDEM = [
    "Como rodar o projeto",
    "Instalação do ambiente",
    "Modelo de dados",
    "Testes",
    "Deploy em produção",
    "Checklist de segurança",
    "Conectar o WhatsApp",
    "Login com o Google",
]

#: Vira a página inicial da Wiki, com o índice acrescentado no fim.
PAGINA_INICIAL = "README.md"


def sem_acento(texto: str) -> str:
    """Remove acentos preservando a letra: "produção" vira "producao"."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def arquivo_da_pagina(titulo: str) -> str:
    """Nome do arquivo na Wiki, sem a extensão.

    Sem acento e sem espaço: o GitHub transforma o nome do arquivo no endereço
    da página, e acento vira código ("Deploy%20em%20produ%C3%A7%C3%A3o").
    """
    limpo = sem_acento(titulo)
    limpo = re.sub(r"[^\w\s-]", "", limpo)
    return re.sub(r"\s+", "-", limpo.strip())


def titulo_do_documento(relativo: str) -> str:
    """O nome escolhido para o documento, ou um derivado do arquivo.

    A derivação é rede de segurança: documento novo aparece na Wiki mesmo que
    ninguém o tenha batizado, em vez de sumir sem aviso.
    """
    if relativo in TITULOS:
        return TITULOS[relativo]
    bruto = Path(relativo).stem.replace("-", " ").replace("_", " ")
    return bruto[:1].upper() + bruto[1:]


def documentos(raiz: Path) -> dict[str, str]:
    """Mapa de caminho no repositório para título na Wiki.

    Varre a pasta docs/ em vez de confiar só na lista fixa, para que documento
    novo nunca fique para trás.
    """
    encontrados: dict[str, str] = {}

    como_rodar = raiz / "COMO-RODAR.md"
    if como_rodar.is_file():
        encontrados["COMO-RODAR.md"] = titulo_do_documento("COMO-RODAR.md")

    pasta = raiz / "docs"
    if pasta.is_dir():
        for arquivo in sorted(pasta.glob("*.md")):
            relativo = f"docs/{arquivo.name}"
            encontrados[relativo] = titulo_do_documento(relativo)

    return encontrados


def _mapa_de_links(raiz: Path) -> dict[str, str]:
    """De caminho de arquivo para nome de página, para trocar nos links."""
    return {
        caminho: arquivo_da_pagina(titulo)
        for caminho, titulo in documentos(raiz).items()
    }


def reescrever_links(texto: str, raiz: Path | None = None) -> str:
    """Troca links de arquivo por links de página da Wiki.

    No repositório, um documento aponta para o outro por caminho de pasta
    ("docs/testes.md"). Na Wiki essa pasta não existe e o link quebra. A Wiki
    referencia a página pelo nome, sem extensão.

    Links para fora (http) e âncoras internas (#secao) não são tocados.
    """
    mapa = _mapa_de_links(raiz) if raiz is not None else {
        caminho: arquivo_da_pagina(titulo) for caminho, titulo in TITULOS.items()
    }

    def trocar(achado: re.Match) -> str:
        alvo = achado.group(2)
        if alvo.startswith(("http://", "https://", "#", "mailto:")):
            return achado.group(0)
        # O link pode vir com âncora: docs/testes.md#cobertura
        caminho, _, ancora = alvo.partition("#")
        caminho = caminho.lstrip("./")
        if caminho not in mapa:
            return achado.group(0)
        destino = mapa[caminho] + (f"#{ancora}" if ancora else "")
        return f"[{achado.group(1)}]({destino})"

    return re.sub(r"\[([^\]]*)\]\(([^)]+)\)", trocar, texto)


def links_do_texto(texto: str) -> list[str]:
    """Os alvos de todos os links internos, para conferir se existem."""
    alvos = []
    for _, alvo in re.findall(r"\[([^\]]*)\]\(([^)]+)\)", texto):
        if alvo.startswith(("http://", "https://", "#", "mailto:")):
            continue
        alvos.append(alvo.partition("#")[0])
    return alvos


def _ordenar(titulos: list[str]) -> list[str]:
    """Na ordem escolhida; o que não estiver na lista vai para o fim."""
    conhecidos = [t for t in ORDEM if t in titulos]
    resto = sorted(t for t in titulos if t not in ORDEM)
    return conhecidos + resto


AVISO = (
    "> Esta página é gerada automaticamente a partir da documentação do\n"
    "> repositório. Para alterá-la, edite o arquivo de origem e envie para a\n"
    "> branch `main`. Edições feitas aqui são perdidas no próximo envio.\n"
)


def montar_menu(titulos: list[str]) -> str:
    """O menu lateral que aparece em todas as páginas da Wiki."""
    linhas = ["### TáEmDia", "", "- [Início](Home)"]
    for titulo in _ordenar(titulos):
        linhas.append(f"- [{titulo}]({arquivo_da_pagina(titulo)})")
    return "\n".join(linhas) + "\n"


def montar_indice(titulos: list[str]) -> str:
    """O índice que fecha a página inicial."""
    linhas = ["", "---", "", "## Documentação", ""]
    for titulo in _ordenar(titulos):
        linhas.append(f"- [{titulo}]({arquivo_da_pagina(titulo)})")
    return "\n".join(linhas) + "\n"


def gerar(raiz: Path, saida: Path) -> dict[str, str]:
    """Escreve a Wiki inteira em `saida`. Devolve título para nome de arquivo."""
    raiz = Path(raiz)
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)

    encontrados = documentos(raiz)
    paginas: dict[str, str] = {}

    for relativo, titulo in encontrados.items():
        origem = raiz / relativo
        texto = reescrever_links(origem.read_text(encoding="utf-8"), raiz)
        nome = arquivo_da_pagina(titulo)
        (saida / f"{nome}.md").write_text(f"{AVISO}\n{texto}", encoding="utf-8")
        paginas[titulo] = nome

    inicial = raiz / PAGINA_INICIAL
    corpo = reescrever_links(inicial.read_text(encoding="utf-8"), raiz) if inicial.is_file() else "# TáEmDia\n"
    indice = montar_indice(list(paginas))
    (saida / "Home.md").write_text(f"{AVISO}\n{corpo}\n{indice}", encoding="utf-8")

    (saida / "_Sidebar.md").write_text(montar_menu(list(paginas)), encoding="utf-8")

    return paginas


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: python scripts/wiki.py <pasta-de-saida>", file=sys.stderr)
        return 2

    raiz = Path(__file__).resolve().parent.parent
    paginas = gerar(raiz, Path(sys.argv[1]))
    print(f"{len(paginas) + 2} páginas geradas em {sys.argv[1]}")
    for titulo, nome in paginas.items():
        print(f"  {titulo} -> {nome}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
