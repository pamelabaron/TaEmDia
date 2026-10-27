"""A análise estática precisa estar ligada de verdade, não só configurada.

Este arquivo nasceu de um defeito que passou despercebido por semanas: o passo
do SonarQube existia no CI, o arquivo de configuração existia na raiz, e mesmo
assim a análise **nunca rodou**. Em toda execução ela aparecia como `skipped`,
que é verde na tela e não chama atenção de ninguém.

A causa é uma regra do GitHub Actions que não está escrita em lugar óbvio: a
condição `if` de um passo **não enxerga o `env` declarado nesse mesmo passo**.
Ela lê o `env` do job. Com `SONAR_TOKEN` declarado só dentro do passo, a
condição comparava contra vazio e pulava, e continuaria pulando mesmo depois de
alguém configurar o segredo.

Três coisas são protegidas aqui:

1. **O token no lugar certo.** No `env` do job, senão a condição não o vê.
2. **A configuração existir e apontar para o projeto certo.** Chave errada
   manda a análise para o projeto de outra pessoa, ou para lugar nenhum.
3. **A cobertura chegar junto.** Análise sem o relatório de cobertura mostra
   0% e faz parecer que o projeto não tem teste, o que seria o oposto da
   verdade: são 492 no backend.
"""
import re

import pytest

from .caminhos import achar, achar_pasta

CI = achar(".github", "workflows", "ci.yml")
PROPRIEDADES = achar("sonar-project.properties")

#: Nome do job que roda a análise. O passo do Sonar vive dentro dele.
JOB = "backend:"


@pytest.fixture(scope="module")
def ci() -> str:
    if CI is None:
        pytest.skip("ci.yml não encontrado")
    return CI.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def propriedades() -> dict[str, str]:
    if PROPRIEDADES is None:
        pytest.skip("sonar-project.properties não encontrado")
    valores = {}
    for linha in PROPRIEDADES.read_text(encoding="utf-8").splitlines():
        limpa = linha.strip()
        if not limpa or limpa.startswith("#") or "=" not in limpa:
            continue
        chave, valor = limpa.split("=", 1)
        valores[chave.strip()] = valor.strip()
    return valores


def _bloco_do_job(texto: str, nome: str) -> str:
    """O trecho do job, do nome dele até o começo do próximo job.

    Os jobs ficam recuados com dois espaços; o seguinte começa na mesma coluna.
    """
    inicio = texto.index(f"  {nome}")
    resto = texto[inicio + 1:]
    achado = re.search(r"\n  \w[\w-]*:\n", resto)
    return resto[: achado.start()] if achado else resto


def _env_do_job(bloco: str) -> str:
    """O bloco `env:` do job, que é o único que a condição `if` enxerga.

    Para distinguir do `env:` de um passo, exige o recuado de job (4 espaços).
    """
    achado = re.search(r"\n    env:\n((?:      .*\n|\n)+)", bloco)
    return achado.group(1) if achado else ""


def test_o_passo_da_analise_existe(ci):
    assert "sonarqube-scan-action" in ci, (
        "Não há passo de análise estática no CI. O playbook do portfólio "
        "pede ferramenta de análise de código."
    )


def test_o_token_esta_no_env_do_job_e_nao_so_no_passo(ci):
    """O defeito que originou este arquivo.

    Declarado só no passo, o token existe para o comando mas **não** para a
    condição que decide se o passo roda. A análise pula em silêncio para
    sempre, e `skipped` não falha o CI nem acende nada.
    """
    bloco = _bloco_do_job(ci, JOB)
    if "sonarqube-scan-action" not in bloco:
        pytest.skip("o passo do Sonar não está neste job")

    assert "SONAR_TOKEN" in _env_do_job(bloco), (
        "SONAR_TOKEN não está no `env` do job. A condição `if` de um passo não "
        "enxerga o `env` declarado no próprio passo: ela lê o do job. Do jeito "
        "que está, a análise aparece como `skipped` em toda execução, mesmo "
        "com o segredo configurado no repositório."
    )


def test_a_condicao_so_depende_de_coisa_que_ela_enxerga(ci):
    """Se a condição citar algo fora do `env` do job, ela é sempre falsa."""
    bloco = _bloco_do_job(ci, JOB)
    if "sonarqube-scan-action" not in bloco:
        pytest.skip("o passo do Sonar não está neste job")

    # A condição do passo do Sonar, se houver.
    trecho = bloco[: bloco.index("sonarqube-scan-action")]
    condicao = re.findall(r"if:\s*(.+)", trecho)
    if not condicao:
        return  # sem condição, o passo sempre roda, e está tudo bem

    usadas = set(re.findall(r"\bsecrets\.(\w+)", condicao[-1]))
    assert not usadas, (
        f"A condição usa secrets.{', secrets.'.join(sorted(usadas))}, e o "
        "contexto `secrets` não está disponível no `if` de um passo. Promova "
        "o segredo a uma variável no `env` do job e compare com ela."
    )


def test_a_configuracao_aponta_para_este_projeto(propriedades):
    assert propriedades.get("sonar.projectKey") == "pamelabaron_TaEmDia", (
        "A chave do projeto não é a deste repositório. Análise com chave "
        "errada não aparece em lugar nenhum, e não dá erro."
    )
    assert propriedades.get("sonar.organization") == "pamelabaron"


def _pasta_existe(caminho: str) -> bool:
    """A pasta existe, vista daqui?

    Dentro do container a pasta `/app` **é** a `backend/`, então "backend/app"
    aparece como "app". No GitHub, onde o repositório inteiro está no disco, o
    caminho é literal. As duas formas valem.
    """
    partes = caminho.strip().split("/")
    if achar_pasta(*partes) is not None:
        return True
    return partes[0] == "backend" and achar_pasta(*partes[1:]) is not None


def test_as_pastas_analisadas_existem(propriedades):
    """Pasta inexistente em `sonar.sources` faz a análise não ver nada."""
    fontes = propriedades.get("sonar.sources", "")
    assert fontes, "sonar.sources está vazio: a análise não teria o que ler."

    faltando = [c.strip() for c in fontes.split(",") if not _pasta_existe(c)]
    assert not faltando, f"Pastas que não existem em sonar.sources: {faltando}"


def test_a_cobertura_do_backend_chega_na_analise(propriedades):
    """Sem o relatório, o painel mostra 0% e parece projeto sem teste."""
    caminho = propriedades.get("sonar.python.coverage.reportPaths")
    assert caminho == "backend/coverage.xml", (
        "O caminho do relatório de cobertura não bate com o que o pytest "
        "gera (ver addopts no backend/pytest.ini)."
    )


def test_os_testes_nao_contam_como_codigo_de_producao(propriedades):
    """Arquivo de teste medido junto distorce a nota e esconde problema real."""
    assert "backend/tests" in propriedades.get("sonar.tests", "")
    exclusoes = propriedades.get("sonar.exclusions", "")
    assert "*.spec.ts" in exclusoes, (
        "Os testes do frontend não estão excluídos das fontes."
    )
