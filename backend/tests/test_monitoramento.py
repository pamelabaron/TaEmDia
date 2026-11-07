"""Monitoramento básico: alguém precisa ficar sabendo quando o site cai.

O critério 4 da avaliação do Demo Day pede "monitoramento básico". Até aqui o
projeto não tinha nenhum: se o sistema caísse de madrugada, a primeira pessoa
a saber seria a vendedora, de manhã, pelo cliente que não recebeu a cobrança.

O monitor é um fluxo agendado do GitHub (.github/workflows/monitor.yml) que
consulta o site de tempos em tempos. Quando a consulta falha, o fluxo fica
vermelho e o GitHub avisa por e-mail. Sem conta nova em serviço nenhum.

Duas coisas protegidas aqui:

1. **O /health tem que dizer a verdade.** Antes ele respondia "ok" sem olhar o
   banco: com o PostgreSQL fora do ar, a API continuava jurando que estava tudo
   bem, e o monitor ficaria verde com o sistema quebrado. Agora ele pergunta ao
   banco e responde 503 quando não há resposta.
2. **O monitor existir, rodar sozinho e vigiar o endereço certo.**
"""
import re

import pytest
import yaml
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app

from .caminhos import achar

MONITOR = achar(".github", "workflows", "monitor.yml")


class TestHealthDizAVerdade:
    def test_com_o_banco_no_ar_responde_ok(self, cliente_http):
        resposta = cliente_http.get("/health")
        assert resposta.status_code == 200
        assert resposta.json()["status"] == "ok"
        assert resposta.json()["banco"] == "ok"

    def test_com_o_banco_fora_responde_503(self, cliente_http):
        """O caso que importa: o processo da API está vivo, o banco não."""

        class BancoFora:
            def execute(self, *_args, **_kwargs):
                raise OperationalError("SELECT 1", {}, Exception("conexão recusada"))

        app.dependency_overrides[get_db] = lambda: BancoFora()
        try:
            resposta = cliente_http.get("/health")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resposta.status_code == 503, (
            "Com o banco fora do ar o /health respondeu sucesso, e o monitor "
            "ficaria verde com o sistema parado."
        )
        assert resposta.json()["banco"] != "ok"

    def test_nao_exige_login(self, cliente_http):
        """Quem consulta é o robô do monitor, que não tem conta."""
        assert cliente_http.get("/health").status_code != 401


@pytest.fixture(scope="module")
def monitor() -> dict:
    """O fluxo lido como YAML, do jeito que o GitHub lê.

    A primeira versão destes testes lia o arquivo como texto e tropeçava nos
    comentários: um comentário entre "schedule:" e "cron:", outro citando "o
    curl" sem "-f". Lendo o YAML, comentário não conta, e é o certo.
    """
    if MONITOR is None:
        pytest.skip("monitor.yml não encontrado")
    return yaml.safe_load(MONITOR.read_text(encoding="utf-8"))


def _gatilhos(fluxo: dict) -> dict:
    # O YAML 1.1 lê a palavra "on" como o booleano True.
    return fluxo.get("on") or fluxo.get(True) or {}


def _comandos(fluxo: dict) -> str:
    """Tudo o que os passos executam, juntando as linhas continuadas por "\\"."""
    blocos = [
        passo.get("run", "")
        for job in fluxo["jobs"].values()
        for passo in job.get("steps", [])
    ]
    return "\n".join(blocos).replace("\\\n", " ")


class TestOMonitorExiste:
    def test_roda_sozinho_de_tempos_em_tempos(self, monitor):
        agenda = _gatilhos(monitor).get("schedule") or []
        assert any("cron" in item for item in agenda), (
            "O monitor precisa de agendamento (schedule/cron). Monitor que só "
            "roda quando alguém lembra não é monitor."
        )

    def test_pode_ser_disparado_na_mao(self, monitor):
        assert "workflow_dispatch" in _gatilhos(monitor)

    def test_vigia_a_api_e_o_site(self, monitor):
        comandos = _comandos(monitor)
        assert "https://taemdia.duckdns.org/api/health" in comandos, (
            "O monitor não consulta a saúde da API."
        )
        assert re.search(r"https://taemdia\.duckdns\.org/(\s|$)", comandos), (
            "O monitor não consulta a página do site."
        )

    def test_confere_o_banco_e_nao_so_o_codigo_http(self, monitor):
        """Um 200 sozinho não basta: o corpo precisa dizer que o banco respondeu."""
        assert '"banco":"ok"' in _comandos(monitor)

    def test_falha_de_verdade_quando_o_site_cai(self, monitor):
        """curl sem -f devolve sucesso até para um erro 502: o passo ficaria
        verde com o site fora do ar."""
        chamadas = re.findall(r"\bcurl\b[^\n]*", _comandos(monitor))
        assert chamadas, "O monitor não faz nenhuma consulta."
        # O -f costuma vir colado com outras opções curtas: "-fsS".
        assert all(re.search(r"\s(-[a-zA-Z]*f[a-zA-Z]*|--fail)(\s|$)", c) for c in chamadas), (
            "Toda chamada do curl precisa de -f (ou --fail), senão um erro do "
            "servidor passa como sucesso."
        )

    def test_insiste_antes_de_acusar(self, monitor):
        """Uma oscilação de rede de um segundo não deve virar alarme."""
        chamadas = re.findall(r"\bcurl\b[^\n]*", _comandos(monitor))
        assert all("--retry" in c for c in chamadas)
