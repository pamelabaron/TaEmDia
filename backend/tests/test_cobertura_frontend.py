"""A conta da cobertura do frontend precisa incluir o site inteiro.

O Karma só mede o que entra na compilação, e só entra o que algum teste
importa. Na primeira medição deu 72%, e o número era falso: o total eram os
9 arquivos que os testes encostavam. Os outros 26 ficavam fora da conta, como
se não existissem. A medição honesta, com tudo dentro, deu 27%.

Por isso existe frontend/src/app/cobertura.spec.ts, que importa todos os
arquivos. Este teste confere que a lista continua completa: arquivo novo que
ninguém importar lá sai da conta, e a meta do playbook (25% no frontend) vira
enfeite sem ninguém perceber.

Vive no pytest, e não no Karma, porque é uma conferência de arquivos no disco:
o próprio arquivo que deveria listar tudo não é quem pode dizer se listou.
"""
import re
from pathlib import Path

import pytest


def _achar(*partes: str) -> Path | None:
    for pasta in Path(__file__).resolve().parents:
        candidato = pasta.joinpath(*partes)
        if candidato.exists():
            return candidato
    return None


FONTE = _achar("frontend", "src", "app")
LISTA = _achar("frontend", "src", "app", "cobertura.spec.ts")

#: Arquivos que não entram na conta e por quê.
DISPENSADOS = {
    # É a própria lista. Importar a si mesmo não faz sentido.
    "cobertura.spec.ts",
    # Ponto de entrada: sobe a aplicação de verdade ao ser importado.
    "main.ts",
}


@pytest.fixture(scope="module")
def arquivos_do_site() -> list[str]:
    if FONTE is None:
        pytest.skip("pasta frontend/src/app não encontrada")
    return sorted(
        str(caminho.relative_to(FONTE)).replace("\\", "/")
        for caminho in FONTE.rglob("*.ts")
        if not caminho.name.endswith(".spec.ts") and caminho.name not in DISPENSADOS
    )


@pytest.fixture(scope="module")
def importados() -> set[str]:
    if LISTA is None:
        pytest.skip("cobertura.spec.ts não encontrado")
    texto = LISTA.read_text(encoding="utf-8")
    return {
        achado.lstrip("./") + ".ts"
        for achado in re.findall(r"^import\s+'([^']+)';", texto, re.M)
    }


def test_todo_arquivo_do_site_entra_na_conta(arquivos_do_site, importados):
    faltando = [arquivo for arquivo in arquivos_do_site if arquivo not in importados]

    assert not faltando, (
        "Arquivos fora da conta da cobertura: "
        + ", ".join(faltando)
        + ". Acrescente cada um a frontend/src/app/cobertura.spec.ts, ou a "
        "porcentagem vai medir só a parte que já tem teste."
    )


def test_a_lista_nao_aponta_para_arquivo_que_sumiu(arquivos_do_site, importados):
    """Arquivo renomeado ou apagado deixaria a compilação dos testes quebrada."""
    conhecidos = set(arquivos_do_site)
    sobrando = [arquivo for arquivo in sorted(importados) if arquivo not in conhecidos]

    assert not sobrando, (
        f"A lista importa arquivos que não existem mais: {sobrando}. "
        "Tire de frontend/src/app/cobertura.spec.ts."
    )


def test_a_meta_de_cobertura_esta_configurada():
    """25% no frontend é exigência do playbook. Meta que ninguém mede não vale."""
    karma = _achar("frontend", "karma.conf.js")
    if karma is None:
        pytest.skip("karma.conf.js não encontrado")

    texto = karma.read_text(encoding="utf-8")
    achado = re.search(r"check:\s*\{\s*global:\s*\{(.*?)\}", texto, re.S)
    assert achado, "Não achei a verificação de cobertura no karma.conf.js"

    metas = {
        nome: int(valor)
        for nome, valor in re.findall(r"(\w+):\s*(\d+)", achado.group(1))
    }
    assert set(metas) == {"statements", "lines", "branches", "functions"}, (
        f"Faltam medidas na meta de cobertura: {sorted(metas)}"
    )
    for nome, valor in metas.items():
        assert valor >= 25, f"A meta de {nome} está em {valor}%, abaixo dos 25% exigidos"
