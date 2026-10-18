"""O agendador precisa rodar em um processo só, em produção.

A API sobe com vários workers, e cada worker é um processo separado: se o
agendador subisse junto com ela, cada processo criaria o seu, e o mesmo cliente
receberia a mesma cobrança uma vez por worker. Furando também o limite diário
da RN10, porque os processos contam as mensagens em paralelo.

Este teste lê o arquivo de produção e trava essa decisão. É o mesmo espírito da
varredura de rotas: uma configuração errada quebra a suíte, não a produção.
"""

import pytest

from .caminhos import achar
import yaml

ARQUIVO = achar("docker-compose.prod.yml")


@pytest.fixture(scope="module")
def servicos() -> dict:
    if ARQUIVO is None:
        pytest.skip("docker-compose.prod.yml não encontrado")
    return yaml.safe_load(ARQUIVO.read_text(encoding="utf-8"))["services"]


def _comando(servico: dict) -> str:
    comando = servico.get("command", "")
    return comando if isinstance(comando, str) else " ".join(comando)


def _ambiente(servico: dict) -> dict:
    ambiente = servico.get("environment", {}) or {}
    if isinstance(ambiente, list):
        return dict(item.split("=", 1) for item in ambiente if "=" in item)
    return {str(c): str(v) for c, v in ambiente.items()}


def _agenda(servico: dict) -> bool:
    """O serviço liga o agendador?"""
    ligado = _ambiente(servico).get("AGENDADOR_ATIVO", "").lower()
    if ligado in ("false", "0", "no"):
        return False
    return "agendador" in _comando(servico) or ligado in ("true", "1", "yes")


def test_existe_exatamente_um_servico_com_agendador(servicos):
    agendam = [nome for nome, s in servicos.items() if _agenda(s)]
    assert len(agendam) == 1, (
        "Em produção o agendador deve rodar em um serviço só. Encontrados: "
        + (", ".join(sorted(agendam)) or "nenhum")
    )


def test_a_api_nao_agenda(servicos):
    """A API é quem roda com vários workers: ela não pode agendar."""
    assert _ambiente(servicos["backend"]).get("AGENDADOR_ATIVO", "").lower() == "false"


def test_o_agendador_roda_em_um_processo_so(servicos):
    nome = next(n for n, s in servicos.items() if _agenda(s))
    comando = _comando(servicos[nome])
    assert "--workers" not in comando, (
        f"O serviço {nome} agenda e usa --workers: cada worker criaria um agendador."
    )


def _origem(servico: dict) -> str:
    """De onde vem o código deste serviço: imagem pronta ou pasta compilada.

    A produção passou a usar imagem já compilada pelo CI, em vez de compilar
    no servidor. A conferência precisa entender as duas formas: a manual, que
    continua valendo como caminho de emergência, e a nova.
    """
    imagem = servico.get("image")
    if imagem:
        return f"image:{imagem}"

    construcao = servico.get("build")
    if isinstance(construcao, dict):
        return "build:" + str(construcao.get("context", ""))
    return f"build:{construcao}"


def test_a_api_e_o_agendador_usam_a_mesma_versao(servicos):
    """Os dois rodam o mesmo código, e isso não pode depender de sorte.

    Se a API subir numa versão e o agendador em outra, o sistema calcula a
    cobrança por uma regra e envia por outra. O estrago é silencioso: nada
    falha, só sai errado.
    """
    da_api = _origem(servicos["backend"])
    do_agendador = _origem(servicos["agendador"])

    assert da_api == do_agendador, (
        f"A API vem de {da_api} e o agendador de {do_agendador}. "
        "Os dois precisam ser a mesma coisa."
    )


def test_nenhum_servico_de_dados_e_recriado_pela_versao(servicos):
    """Banco e volumes não acompanham a versão do código.

    Marcar o Postgres com a versão do commit faria cada subida trocar o
    container do banco. Os dados sobrevivem (estão no volume), mas é risco
    gratuito num sistema que guarda clientes e comprovantes.
    """
    origem = _origem(servicos["db"])
    assert "${VERSAO" not in origem and "$VERSAO" not in origem, (
        f"O banco está marcado com a versão do código ({origem})."
    )
