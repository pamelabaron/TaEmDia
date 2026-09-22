"""Processo dedicado do agendador de cobranças.

Em produção a API sobe com vários workers, e cada worker é um processo
separado. Se o agendador subisse dentro dela, cada processo criaria o seu, e o
mesmo cliente receberia a mesma cobrança uma vez por worker — furando também o
limite diário da RN10, porque os processos contariam as mensagens em paralelo.

Por isso o agendador roda aqui: um container, um processo, um agendador. A API
sobe com AGENDADOR_ATIVO=false.

Uso: python -m app.agendador_main
"""
import logging
import signal
import threading

from app.core.config import settings
from app.modules.agente.agendador import iniciar_agendador, parar_agendador

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    if settings.em_producao:
        problemas = settings.validar_para_producao()
        if problemas:
            raise RuntimeError(
                "Configuração insegura para produção: " + "; ".join(problemas)
            )

    iniciar_agendador()
    logger.info("Agendador em processo dedicado. Aguardando os horários.")

    # Fica vivo até o Docker mandar parar, e então encerra o agendador com
    # calma, em vez de morrer no meio de um envio.
    encerrar = threading.Event()

    def _ao_receber_sinal(*_args) -> None:
        logger.info("Sinal de parada recebido; encerrando o agendador.")
        encerrar.set()

    signal.signal(signal.SIGTERM, _ao_receber_sinal)
    signal.signal(signal.SIGINT, _ao_receber_sinal)

    try:
        encerrar.wait()
    finally:
        parar_agendador()


if __name__ == "__main__":
    main()
