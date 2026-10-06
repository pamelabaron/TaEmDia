"""As regras de cliente existem em dois idiomas. Elas não podem discordar.

A validação de CPF e telefone vive em Python (que decide) e em TypeScript
(que avisa a pessoa antes de ela mandar o formulário). Duplicar era a escolha
certa: sem a cópia no site, cada dígito errado custaria uma ida ao servidor.

O risco da duplicação é o desencontro. Alguém acrescenta um DDD novo de um
lado e esquece do outro, e aí o site aceita um número que a API recusa, ou
pior: o site recusa um cliente real e o vendedor acha que o sistema quebrou.

Este teste lê o arquivo do frontend como texto e compara com o do backend.
É o mesmo recurso usado em test_rotas_no_nginx.py para comparar as rotas do
Angular com a configuração do Nginx.
"""
import re
from pathlib import Path

import pytest

from app.modules.clientes.regras import (
    CODIGO_PAIS_PADRAO,
    DDDS_VALIDOS,
    DIGITOS_DO_CPF,
)


def _achar(*partes: str) -> Path | None:
    for pasta in Path(__file__).resolve().parents:
        candidato = pasta.joinpath(*partes)
        if candidato.is_file():
            return candidato
    return None


REGRAS_TS = _achar("frontend", "src", "app", "core", "regras-cliente.ts")


@pytest.fixture(scope="module")
def texto_do_frontend() -> str:
    if REGRAS_TS is None:
        pytest.skip("regras-cliente.ts não encontrado")
    return REGRAS_TS.read_text(encoding="utf-8")


def _ddds_do_frontend(texto: str) -> set[str]:
    trecho = re.search(r"DDDS_VALIDOS[^=]*=\s*new Set\(\[(.*?)\]\)", texto, re.S)
    assert trecho, "Não achei a lista DDDS_VALIDOS no arquivo do frontend"
    return set(re.findall(r"'(\d{2})'", trecho.group(1)))


def test_a_lista_de_ddds_e_a_mesma_nos_dois_lados(texto_do_frontend):
    do_site = _ddds_do_frontend(texto_do_frontend)

    faltando_no_site = DDDS_VALIDOS - do_site
    sobrando_no_site = do_site - set(DDDS_VALIDOS)

    assert not faltando_no_site, (
        f"DDDs que a API aceita e o site recusa: {sorted(faltando_no_site)}. "
        "Acrescente em frontend/src/app/core/regras-cliente.ts."
    )
    assert not sobrando_no_site, (
        f"DDDs que o site aceita e a API recusa: {sorted(sobrando_no_site)}. "
        "Acrescente em backend/app/modules/clientes/regras.py."
    )


def test_o_codigo_do_pais_padrao_e_o_mesmo(texto_do_frontend):
    achado = re.search(r"CODIGO_PAIS_PADRAO\s*=\s*'(\d+)'", texto_do_frontend)
    assert achado, "Não achei CODIGO_PAIS_PADRAO no arquivo do frontend"
    assert achado.group(1) == CODIGO_PAIS_PADRAO


def test_o_tamanho_do_cpf_e_o_mesmo(texto_do_frontend):
    achado = re.search(r"DIGITOS_DO_CPF\s*=\s*(\d+)", texto_do_frontend)
    assert achado, "Não achei DIGITOS_DO_CPF no arquivo do frontend"
    assert int(achado.group(1)) == DIGITOS_DO_CPF


def test_os_tamanhos_de_numero_brasileiro_sao_os_mesmos(texto_do_frontend):
    from app.modules.clientes.regras import TAMANHOS_BRASIL

    achado = re.search(r"TAMANHOS_BRASIL\s*=\s*\[([\d,\s]+)\]", texto_do_frontend)
    assert achado, "Não achei TAMANHOS_BRASIL no arquivo do frontend"
    do_site = tuple(int(n) for n in re.findall(r"\d+", achado.group(1)))
    assert do_site == TAMANHOS_BRASIL
