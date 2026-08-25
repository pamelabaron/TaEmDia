"""Camada de abstração do WhatsApp (RFC 5.3.7).

Nenhum outro módulo importa a biblioteca de integração diretamente: todos falam
com a interface `WhatsAppClient`. Isso permite trocar a implementação (simulador
<-> Evolution API) sem alterar o resto do sistema.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResultadoEnvio:
    """Resultado de uma tentativa de envio."""
    sucesso: bool
    detalhe: str = ""


@dataclass
class StatusConexao:
    """Estado da conexão com o WhatsApp."""
    conectado: bool
    numero: str | None = None
    qrcode: str | None = None  # imagem base64 para escanear, quando desconectado
    detalhe: str = ""


class WhatsAppClient(Protocol):
    """Contrato que qualquer implementação de WhatsApp deve cumprir."""

    def enviar_mensagem(self, numero: str, texto: str) -> ResultadoEnvio: ...

    def status(self) -> StatusConexao: ...

    def desconectar(self) -> None: ...


class SimuladorWhatsAppClient:
    """Implementação de teste: não envia nada de verdade, apenas registra no log.

    Usada enquanto o número real não está conectado, permitindo testar todo o
    fluxo de cobrança (agendamento, templates, regras e histórico) sem depender
    do celular.
    """

    def __init__(self) -> None:
        self.enviadas: list[tuple[str, str]] = []

    def enviar_mensagem(self, numero: str, texto: str) -> ResultadoEnvio:
        self.enviadas.append((numero, texto))
        logger.info("[SIMULADOR] Mensagem para %s: %s", numero, texto)
        return ResultadoEnvio(sucesso=True, detalhe="simulado")

    def status(self) -> StatusConexao:
        return StatusConexao(
            conectado=True,
            numero="(simulador)",
            detalhe="Modo simulador: as mensagens são registradas, mas não enviadas.",
        )

    def desconectar(self) -> None:
        self.enviadas.clear()


class EvolutionWhatsAppClient:
    """Implementação real sobre a Evolution API (REST sobre o WhatsApp Web)."""

    def __init__(self, base_url: str, api_key: str, instancia: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.instancia = instancia

    @property
    def _headers(self) -> dict:
        return {"apikey": self.api_key, "Content-Type": "application/json"}

    def enviar_mensagem(self, numero: str, texto: str) -> ResultadoEnvio:
        url = f"{self.base_url}/message/sendText/{self.instancia}"
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.post(
                    url, headers=self._headers,
                    json={"number": numero, "text": texto},
                )
            if resp.status_code < 300:
                return ResultadoEnvio(sucesso=True, detalhe=str(resp.status_code))
            return ResultadoEnvio(sucesso=False, detalhe=f"HTTP {resp.status_code}: {resp.text[:200]}")
        except httpx.HTTPError as erro:
            return ResultadoEnvio(sucesso=False, detalhe=f"Falha de conexão: {erro}")

    def status(self) -> StatusConexao:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"{self.base_url}/instance/connectionState/{self.instancia}",
                    headers=self._headers,
                )
                if resp.status_code >= 300:
                    return self._pedir_qrcode(client, f"HTTP {resp.status_code}")
                estado = (resp.json().get("instance") or {}).get("state", "")
                if estado == "open":
                    return StatusConexao(conectado=True, detalhe="Conectado.")
                return self._pedir_qrcode(client, f"Estado: {estado or 'desconhecido'}")
        except httpx.HTTPError as erro:
            return StatusConexao(conectado=False, detalhe=f"Evolution API indisponível: {erro}")

    def _pedir_qrcode(self, client: httpx.Client, detalhe: str) -> StatusConexao:
        """Busca o QR Code para o vendedor escanear e conectar o número."""
        try:
            resp = client.get(
                f"{self.base_url}/instance/connect/{self.instancia}",
                headers=self._headers,
            )
            dados = resp.json() if resp.status_code < 300 else {}
            qr = dados.get("base64") or dados.get("qrcode", {}).get("base64")
            return StatusConexao(conectado=False, qrcode=qr, detalhe=detalhe)
        except (httpx.HTTPError, ValueError):
            return StatusConexao(conectado=False, detalhe=detalhe)

    def desconectar(self) -> None:
        try:
            with httpx.Client(timeout=15) as client:
                client.delete(
                    f"{self.base_url}/instance/logout/{self.instancia}",
                    headers=self._headers,
                )
        except httpx.HTTPError:
            logger.warning("Falha ao desconectar a instância do WhatsApp.")


_simulador = SimuladorWhatsAppClient()


def get_whatsapp_client() -> WhatsAppClient:
    """Escolhe a implementação conforme a configuração.

    Sem `EVOLUTION_API_KEY` preenchida, o sistema roda em modo simulador — o que
    permite usar e demonstrar todo o fluxo sem um número conectado.
    """
    if settings.EVOLUTION_API_URL and settings.EVOLUTION_API_KEY:
        return EvolutionWhatsAppClient(
            base_url=settings.EVOLUTION_API_URL,
            api_key=settings.EVOLUTION_API_KEY,
            instancia=settings.EVOLUTION_INSTANCIA,
        )
    return _simulador
