"""Um teste de guarda que pula não está guardando nada.

Vários testes leem arquivos do resto do repositório para conferir configuração:
as rotas do Angular contra o Nginx, o docker-compose de produção, a lista da
cobertura do frontend. Todos começam procurando o arquivo, e todos têm a mesma
saída de emergência: se não acharem, pulam com um aviso.

A saída existe por um bom motivo (o arquivo pode faltar numa checagem parcial),
mas ela tem um custo: pytest conta teste pulado como "não falhou". A suíte fica
verde, o relatório diz "456 passed", e ninguém repara que a guarda mais
importante não rodou.

Este arquivo fecha essa porta: aqui, não achar o arquivo é **falha**, não
aviso. Se a busca quebrar, é este teste que grita.
"""
import importlib

import pytest

#: Cada guarda e o que ela precisa ter encontrado para valer alguma coisa.
GUARDAS = {
    "test_topologia_producao": [("ARQUIVO", "docker-compose.prod.yml")],
    "test_rotas_no_nginx": [
        ("CONF", "docker/nginx/taemdia.conf"),
        ("ROTAS_ANGULAR", "frontend/src/app/app.routes.ts"),
    ],
    "test_wiki": [("GERADOR", "scripts/wiki.py"), ("DOCS", "pasta docs/")],
    "test_regras_espelhadas": [("REGRAS_TS", "frontend/src/app/core/regras-cliente.ts")],
    "test_cobertura_frontend": [
        ("FONTE", "pasta frontend/src/app"),
        ("LISTA", "frontend/src/app/cobertura.spec.ts"),
    ],
    "test_limites_nos_formularios": [("TELAS", "pasta frontend/src/app/pages")],
}


@pytest.mark.parametrize(
    "modulo, constante, descricao",
    [(m, c, d) for m, alvos in GUARDAS.items() for c, d in alvos],
)
def test_a_guarda_achou_o_arquivo_que_confere(modulo, constante, descricao):
    mod = importlib.import_module(f"tests.{modulo}")
    achado = getattr(mod, constante, "ausente")

    assert achado != "ausente", (
        f"{modulo} não tem mais a constante {constante}. "
        "Se ela mudou de nome, atualize a lista aqui."
    )
    assert achado is not None, (
        f"{modulo} não encontrou {descricao}, então os testes dele vão **pular** "
        "em silêncio e a conferência não acontece. "
        "Confira se o arquivo existe e se não é um arquivo vazio: restos de "
        "montagem do Docker já enganaram essa busca antes."
    )


def test_arquivo_vazio_nao_conta_como_achado(tmp_path, monkeypatch):
    """A regra que corrigiu o CI, testada diretamente.

    Um `docker-compose.prod.yml` de 0 bytes dentro de backend/ fazia a busca
    parar nele, antes de chegar ao arquivo de verdade na raiz. O CI ficou
    vermelho cinco envios seguidos por isso.
    """
    from tests import caminhos

    raiz = tmp_path / "repo"
    perto = raiz / "backend" / "tests"
    perto.mkdir(parents=True)

    (raiz / "alvo.txt").write_text("conteudo de verdade", encoding="utf-8")
    (raiz / "backend" / "alvo.txt").write_text("", encoding="utf-8")  # o resto de montagem

    monkeypatch.setattr(caminhos, "__file__", str(perto / "caminhos.py"))

    achado = caminhos.achar("alvo.txt")
    assert achado is not None, "a busca desistiu em vez de continuar subindo"
    assert achado.read_text(encoding="utf-8") == "conteudo de verdade"
    assert achado.parent.name == "repo", "achou o vazio de backend/ em vez do de verdade"


def test_pasta_vazia_nao_conta_como_achada(tmp_path, monkeypatch):
    """O Docker também cria pasta vazia ao montar uma pasta de fora."""
    from tests import caminhos

    raiz = tmp_path / "repo"
    perto = raiz / "backend" / "tests"
    perto.mkdir(parents=True)

    (raiz / "docs").mkdir()
    (raiz / "docs" / "algo.md").write_text("texto", encoding="utf-8")
    (raiz / "backend" / "docs").mkdir()  # o resto de montagem, vazio

    monkeypatch.setattr(caminhos, "__file__", str(perto / "caminhos.py"))

    achada = caminhos.achar_pasta("docs")
    assert achada is not None
    assert achada.parent.name == "repo", "achou a pasta vazia de backend/"
