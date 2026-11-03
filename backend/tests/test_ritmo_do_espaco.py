"""O espaço entre as coisas precisa dizer o que pertence a quê (RN-L02).

Vão igual em todo lugar é vão que ninguém escolheu. Antes desta escala, as
telas usavam **doze** valores diferentes, decididos um a um, e o pior deles era
o 16px: ele separava tanto dois itens de uma mesma lista quanto duas seções
inteiras. Com a mesma distância nos dois papéis, a estrutura desaparece e a
tela vira uma pilha de coisas igualmente distantes.

A escala não resolve pelo valor, resolve pela proporção: apertado dentro do
grupo, largo entre grupos, muito largo entre seções. É a diferença entre os
três que o olho lê como organização.

Esta varredura lê os arquivos, como as outras guardas do projeto, e confere
duas coisas: que a escala existe e cresce, e que as telas usam a escala em vez
de números soltos no lugar onde o ritmo aparece.
"""
import re

import pytest

from .caminhos import achar, achar_pasta

ESTILOS = achar("frontend", "src", "styles.scss")
TELAS = achar_pasta("frontend", "src", "app", "pages")

#: Os degraus, do mais apertado ao mais largo.
DEGRAUS = ["--vao-apertado", "--vao-dentro", "--vao-grupo", "--vao-secao"]


@pytest.fixture(scope="module")
def escala() -> dict[str, int]:
    if ESTILOS is None:
        pytest.skip("styles.scss não encontrado")

    texto = ESTILOS.read_text(encoding="utf-8")
    achados = {}
    for nome in DEGRAUS:
        m = re.search(rf"{re.escape(nome)}:\s*(\d+)px", texto)
        if m:
            achados[nome] = int(m.group(1))
    return achados


def test_a_escala_existe_inteira(escala):
    faltando = [nome for nome in DEGRAUS if nome not in escala]
    assert not faltando, (
        f"Degraus que faltam na escala de espaço: {faltando}. "
        "Estão em frontend/src/styles.scss, no :root."
    )


def test_cada_degrau_e_maior_que_o_anterior(escala):
    """Dois degraus com o mesmo valor são um degrau só, e não criam ritmo."""
    if len(escala) < len(DEGRAUS):
        pytest.skip("a escala está incompleta; o teste anterior cobre isso")

    valores = [escala[nome] for nome in DEGRAUS]
    for anterior, seguinte, nome_a, nome_b in zip(
        valores, valores[1:], DEGRAUS, DEGRAUS[1:]
    ):
        assert seguinte > anterior, (
            f"{nome_b} ({seguinte}px) não é maior que {nome_a} ({anterior}px)"
        )


def test_a_seccao_se_separa_bem_mais_que_o_item(escala):
    """A proporção é o que se lê, não o valor.

    Menos que o dobro e a diferença passa despercebida: o olho não distingue
    24px de 30px numa tela cheia, mas distingue 12px de 44px na hora.
    """
    if len(escala) < len(DEGRAUS):
        pytest.skip("a escala está incompleta")

    assert escala["--vao-secao"] >= escala["--vao-dentro"] * 2, (
        f"O vão de seção ({escala['--vao-secao']}px) precisa ser pelo menos o "
        f"dobro do vão entre itens ({escala['--vao-dentro']}px), senão a "
        "separação não se percebe."
    )


def test_as_telas_separam_blocos_pela_escala():
    """Bloco com margem em número solto escapa do ritmo sem ninguém notar."""
    if TELAS is None:
        pytest.skip("pasta das telas não encontrada")

    fora_da_escala = []
    for arquivo in sorted(TELAS.rglob("*.component.ts")):
        texto = arquivo.read_text(encoding="utf-8")
        for achado in re.finditer(
            r"\.(?:bloco|form-card|venda-card|kpis|abas)[^{]*\{[^}]*?"
            r"margin-bottom:\s*(\d+)px",
            texto,
            re.S,
        ):
            linha = texto[: achado.start()].count("\n") + 1
            fora_da_escala.append(f"{arquivo.name}:{linha} ({achado.group(1)}px)")

    assert not fora_da_escala, (
        "Blocos separados por número solto em vez da escala: "
        + ", ".join(fora_da_escala)
        + ". Use var(--vao-secao) ou var(--vao-grupo)."
    )
