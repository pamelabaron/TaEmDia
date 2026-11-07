"""Testes da camada de abstração do WhatsApp (simulador e Evolution API)."""
import httpx

from app.modules.whatsapp.client import (
    EvolutionWhatsAppClient,
    SimuladorWhatsAppClient,
    get_whatsapp_client,
)


class RespostaFalsa:
    """Resposta HTTP simulada, para não depender da Evolution API real."""

    def __init__(self, status_code=200, dados=None, texto=""):
        self.status_code = status_code
        self._dados = dados or {}
        self.text = texto

    def json(self):
        return self._dados


def _instalar_cliente_falso(monkeypatch, respostas, erro=None):
    class ClienteFalso:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def _resolver(self, url=""):
            if erro is not None:
                raise erro
            if "/instance/connect/" in url:
                return respostas.get("connect")
            return respostas.get("state", respostas.get("post"))

        def post(self, url="", **kw):
            if erro is not None:
                raise erro
            return respostas.get("post")

        def get(self, url="", **kw):
            return self._resolver(url)

        def delete(self, url="", **kw):
            if erro is not None:
                raise erro
            return respostas.get("delete")

    monkeypatch.setattr(httpx, "Client", ClienteFalso)
    return EvolutionWhatsAppClient("http://evolution:8080", "chave", "taemdia")


class TestSimulador:
    def test_registra_sem_enviar(self):
        cliente = SimuladorWhatsAppClient()
        resultado = cliente.enviar_mensagem("5547999990001", "Ola")
        assert resultado.sucesso is True
        assert cliente.enviadas == [("5547999990001", "Ola")]

    def test_acumula_as_mensagens(self):
        cliente = SimuladorWhatsAppClient()
        cliente.enviar_mensagem("1", "a")
        cliente.enviar_mensagem("2", "b")
        assert len(cliente.enviadas) == 2

    def test_status_sempre_conectado(self):
        assert SimuladorWhatsAppClient().status().conectado is True

    def test_desconectar_limpa_o_historico(self):
        cliente = SimuladorWhatsAppClient()
        cliente.enviar_mensagem("1", "a")
        cliente.desconectar()
        assert cliente.enviadas == []


class TestSelecaoDaImplementacao:
    def test_sem_chave_usa_o_simulador(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "")
        assert isinstance(get_whatsapp_client(), SimuladorWhatsAppClient)

    def test_com_chave_usa_a_evolution(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "EVOLUTION_API_URL", "http://evolution:8080")
        monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "chave")
        assert isinstance(get_whatsapp_client(), EvolutionWhatsAppClient)


class TestEvolutionEnvio:
    def test_envio_bem_sucedido(self, monkeypatch):
        cliente = _instalar_cliente_falso(monkeypatch, {"post": RespostaFalsa(201)})
        assert cliente.enviar_mensagem("5547999990001", "Ola").sucesso is True

    def test_erro_http_retorna_falha(self, monkeypatch):
        cliente = _instalar_cliente_falso(
            monkeypatch, {"post": RespostaFalsa(400, texto="numero invalido")}
        )
        resultado = cliente.enviar_mensagem("x", "Ola")
        assert resultado.sucesso is False
        assert "400" in resultado.detalhe

    def test_falha_de_conexao_e_tratada(self, monkeypatch):
        cliente = _instalar_cliente_falso(monkeypatch, {}, erro=httpx.ConnectError("sem rede"))
        resultado = cliente.enviar_mensagem("5547999990001", "Ola")
        assert resultado.sucesso is False
        assert "Falha de conexao" in resultado.detalhe.replace("ã", "a")


class TestEvolutionStatus:
    def test_instancia_conectada(self, monkeypatch):
        cliente = _instalar_cliente_falso(
            monkeypatch, {"state": RespostaFalsa(200, {"instance": {"state": "open"}})}
        )
        assert cliente.status().conectado is True

    def test_desconectada_traz_o_qrcode(self, monkeypatch):
        cliente = _instalar_cliente_falso(monkeypatch, {
            "state": RespostaFalsa(200, {"instance": {"state": "close"}}),
            "connect": RespostaFalsa(200, {"base64": "data:image/png;base64,XXX"}),
        })
        status = cliente.status()
        assert status.conectado is False
        assert status.qrcode == "data:image/png;base64,XXX"

    def test_servico_indisponivel(self, monkeypatch):
        cliente = _instalar_cliente_falso(monkeypatch, {}, erro=httpx.ConnectError("sem rede"))
        status = cliente.status()
        assert status.conectado is False
        assert "indispon" in status.detalhe

    def test_desconectar_nao_quebra_com_erro(self, monkeypatch):
        cliente = _instalar_cliente_falso(monkeypatch, {}, erro=httpx.ConnectError("sem rede"))
        cliente.desconectar()  # não deve levantar exceção
