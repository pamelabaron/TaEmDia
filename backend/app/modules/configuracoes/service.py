"""Regras das configurações do agente de cobrança."""
import uuid

from app.modules.configuracoes.repository import ConfiguracaoRepository
from app.modules.configuracoes.schemas import ConfiguracaoUpdate
from app.modules.vendedores.models import Configuracao


class ConfiguracaoService:
    def __init__(self, repo: ConfiguracaoRepository):
        self.repo = repo

    def obter(self, vendedor_id: uuid.UUID) -> Configuracao:
        """Busca as configurações; na primeira vez cria com os valores padrão."""
        config = self.repo.buscar(vendedor_id)
        if config is None:
            config = self.repo.criar(vendedor_id)
        return config

    def atualizar(self, vendedor_id: uuid.UUID, dados: ConfiguracaoUpdate) -> Configuracao:
        config = self.obter(vendedor_id)
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(config, campo, valor)
        self.repo.salvar()
        return config
