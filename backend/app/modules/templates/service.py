"""Regras de negócio dos templates de mensagem.

Variáveis dinâmicas suportadas nos templates:
  {nome_cliente}  {valor_parcela}  {data_vencimento}  {dias_atraso}
"""
import uuid

from app.modules.templates.models import TemplateMensagem
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.schemas import TemplateUpdate

VARIAVEIS = ["nome_cliente", "valor_parcela", "data_vencimento", "dias_atraso"]

# Templates padrão pré-configurados, criados na primeira vez que o vendedor acessa.
TEMPLATES_PADRAO = {
    "lembrete": {
        "titulo": "Lembrete de vencimento",
        "corpo": (
            "Olá {nome_cliente}! 😊 Passando para lembrar que sua parcela de "
            "{valor_parcela} vence em {data_vencimento}. Qualquer dúvida, estou à disposição."
        ),
    },
    "vencimento": {
        "titulo": "Vence hoje",
        "corpo": (
            "Olá {nome_cliente}! Sua parcela de {valor_parcela} vence hoje "
            "({data_vencimento}). Obrigada pela preferência!"
        ),
    },
    "atraso": {
        "titulo": "Parcela em atraso",
        "corpo": (
            "Olá {nome_cliente}! Consta um valor de {valor_parcela} em aberto desde "
            "{data_vencimento} ({dias_atraso} dia(s) de atraso). Podemos combinar o pagamento?"
        ),
    },
}

# Dados de exemplo para a pré-visualização.
EXEMPLO = {
    "nome_cliente": "Maria Silva",
    "valor_parcela": "R$ 100,00",
    "data_vencimento": "10/08/2026",
    "dias_atraso": "3",
}


def renderizar(corpo: str, contexto: dict) -> str:
    """Substitui as variáveis {chave} pelos valores do contexto. Variáveis
    desconhecidas são mantidas como estão (não quebra)."""
    resultado = corpo
    for chave in VARIAVEIS:
        if chave in contexto:
            resultado = resultado.replace("{" + chave + "}", str(contexto[chave]))
    return resultado


class TemplateNaoEncontradoError(Exception):
    pass


class TemplateService:
    def __init__(self, repo: TemplateRepository):
        self.repo = repo

    def listar(self, vendedor_id: uuid.UUID) -> list[TemplateMensagem]:
        templates = self.repo.listar(vendedor_id)
        if not templates:
            templates = self._criar_padroes(vendedor_id)
        return templates

    def _criar_padroes(self, vendedor_id: uuid.UUID) -> list[TemplateMensagem]:
        novos = [
            TemplateMensagem(
                vendedor_id=vendedor_id, tipo=tipo,
                titulo=dados["titulo"], corpo=dados["corpo"], is_padrao=True,
            )
            for tipo, dados in TEMPLATES_PADRAO.items()
        ]
        self.repo.criar_varios(novos)
        return self.repo.listar(vendedor_id)

    def editar(self, vendedor_id: uuid.UUID, template_id: uuid.UUID, dados: TemplateUpdate) -> TemplateMensagem:
        template = self.repo.buscar_por_id(vendedor_id, template_id)
        if not template:
            raise TemplateNaoEncontradoError()
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(template, campo, valor)
        self.repo.salvar()
        return template

    def preview(self, corpo: str) -> str:
        return renderizar(corpo, EXEMPLO)
