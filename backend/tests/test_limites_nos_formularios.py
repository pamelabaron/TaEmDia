"""Todo campo do formulário precisa de limite também na tela (RN-L01).

A API já recusa valor fora da faixa, e ela é quem decide. Mas deixar a tela
sem limite tem custo próprio:

- a pessoa digita um texto longo, clica em salvar, espera, e só então descobre
  que não cabia. O limite no campo simplesmente não deixa passar do tamanho;
- campo numérico com "max" no HTML **não impede digitar** 999999. O navegador
  só marca como inválido, e o site mandava assim mesmo.

Esta varredura lê os arquivos das telas e reprova campo sem limite. Vive no
pytest, e não no Karma, porque é conferência de texto nos arquivos: o mesmo
recurso já usado para comparar as rotas do Angular com o Nginx.
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


TELAS = _achar("frontend", "src", "app", "pages")

def _tem_faixa(marca: str) -> bool:
    """Declara mínimo e máximo?

    Aceita as duas formas: o atributo fixo do HTML (`min="1"`) e a ligação do
    Angular a um valor calculado (`[min]="dataMinima"`), que é o que se usa
    quando a faixa depende da data de hoje.
    """
    return all(
        re.search(rf"\[?{limite}\]?\s*=", marca) for limite in ("min", "max")
    )


def _campos_do_arquivo(texto: str) -> list[tuple[int, str]]:
    """Cada <input> ou <textarea> da tela, com a linha onde começa.

    Pega a marcação inteira, mesmo quebrada em várias linhas, porque o atributo
    do limite costuma ficar na linha de baixo.
    """
    achados = []
    for marca in re.finditer(r"<(input|textarea)\b[^>]*>", texto, re.S):
        if "matInput" not in marca.group(0):
            continue
        linha = texto[: marca.start()].count("\n") + 1
        achados.append((linha, " ".join(marca.group(0).split())))
    return achados


@pytest.fixture(scope="module")
def campos() -> list[tuple[str, int, str]]:
    if TELAS is None:
        pytest.skip("pasta das telas não encontrada")

    todos = []
    for arquivo in sorted(TELAS.rglob("*.component.ts")):
        texto = arquivo.read_text(encoding="utf-8")
        for linha, marca in _campos_do_arquivo(texto):
            todos.append((arquivo.name, linha, marca))
    return todos


def test_a_varredura_enxerga_os_campos_das_telas(campos):
    """Varredura vazia faria os outros testes passarem sem testar nada."""
    assert len(campos) >= 10, f"A varredura achou poucos campos: {len(campos)}"
    assert any("clientes.component.ts" in arquivo for arquivo, _, _ in campos)


def test_todo_campo_de_texto_tem_tamanho_maximo(campos):
    sem_limite = [
        f"{arquivo}:{linha}"
        for arquivo, linha, marca in campos
        if 'type="number"' not in marca
        and 'type="date"' not in marca
        and "maxlength" not in marca
    ]

    assert not sem_limite, (
        "Campos de texto sem maxlength: "
        + ", ".join(sem_limite)
        + ". Acrescente maxlength no <input>, com o mesmo valor da API."
    )


def test_todo_campo_de_numero_declara_a_faixa(campos):
    """min e max no HTML não impedem digitar, mas marcam o campo como inválido.

    São o aviso visual. Quem impede de fato é a conferência antes do envio,
    coberta pelos testes de cada tela no Karma.
    """
    sem_faixa = [
        f"{arquivo}:{linha}"
        for arquivo, linha, marca in campos
        if 'type="number"' in marca and not _tem_faixa(marca)
    ]

    assert not sem_faixa, (
        "Campos numéricos sem min e max: "
        + ", ".join(sem_faixa)
        + ". Acrescente os dois, com os mesmos valores da API."
    )


def test_todo_campo_de_data_declara_a_faixa(campos):
    """Sem min e max, o calendário do navegador aceita o ano 9999."""
    sem_faixa = [
        f"{arquivo}:{linha}"
        for arquivo, linha, marca in campos
        if 'type="date"' in marca and not _tem_faixa(marca)
    ]

    assert not sem_faixa, (
        "Campos de data sem faixa: "
        + ", ".join(sem_faixa)
        + ". Acrescente [min] e [max] no <input>."
    )
