"""O agendador precisa rodar em um processo só, em produção.

A API sobe com vários workers, e cada worker é um processo separado: se o
agendador subisse junto com ela, cada processo criaria o seu, e o mesmo cliente
receberia a mesma cobrança uma vez por worker — furando também o limite diário
da RN10, porque os processos contam as mensagens em paralelo.

Este teste lê o arquivo de produção e trava essa decisão. É o mesmo espírito da
varredura de rotas: uma configuração errada quebra a suíte, não a produção.
"""
from pathlib import Path

import pytest
import yaml

def _achar_arquivo() -> Path | None:
    """Procura o compose de produção subindo a partir deste arquivo.

    Nos testes em container só a pasta backend é montada, então o arquivo entra
    num nível diferente do que ele ocupa no repositório.
    """
    for pasta in Path(__file__).resolve().parents:
        candidato = pasta / "docker-compose.prod.yml"
        if candidato.is_file():
            return candidato
    return None


ARQUIVO = _achar_arquivo()


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
