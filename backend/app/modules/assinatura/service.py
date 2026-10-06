"""Regras de negócio da assinatura. Não toca no banco: fala com o repositório."""
import uuid
from datetime import date, datetime

from app.modules.assinatura import regras
from app.modules.assinatura.models import Assinatura, PagamentoAssinatura
from app.modules.assinatura.repository import AssinaturaRepository


class AssinaturaService:
    def __init__(self, repo: AssinaturaRepository) -> None:
        self.repo = repo

    # --- vigência -----------------------------------------------------------

    def _vigencia(self, vendedor_id: uuid.UUID) -> regras.Vigencia | None:
        linha = self.repo.buscar(vendedor_id)
        if linha is None:
            return None
        return regras.Vigencia(valido_ate=linha.valido_ate, origem=linha.origem)

    def iniciar_teste(self, vendedor_id: uuid.UUID, hoje: date | None = None) -> Assinatura:
        """RN-A01. Chamado uma vez, quando a conta é criada."""
        hoje = hoje or date.today()
        existente = self.repo.buscar(vendedor_id)
        if existente is not None:
            return existente
        v = regras.inicio_do_teste(hoje)
        return self.repo.salvar(
            Assinatura(vendedor_id=vendedor_id, valido_ate=v.valido_ate, origem=v.origem)
        )

    def situacao(self, vendedor_id: uuid.UUID, hoje: date | None = None) -> str:
        return regras.situacao(self._vigencia(vendedor_id), hoje or date.today())

    def pode_escrever(self, vendedor_id: uuid.UUID, hoje: date | None = None) -> bool:
        return regras.pode_escrever(self._vigencia(vendedor_id), hoje or date.today())

    def resumo(self, vendedor_id: uuid.UUID, hoje: date | None = None) -> dict:
        """O que a tela "Minha assinatura" mostra."""
        hoje = hoje or date.today()
        linha = self.repo.buscar(vendedor_id)
        vigencia = (
            regras.Vigencia(valido_ate=linha.valido_ate, origem=linha.origem) if linha else None
        )
        situacao = regras.situacao(vigencia, hoje)
        dias = (linha.valido_ate - hoje).days if linha else 0
        return {
            "situacao": situacao,
            "valido_ate": linha.valido_ate if linha else None,
            "dias_restantes": max(dias, 0),
            "tem_pendente": self.repo.pendente_do_vendedor(vendedor_id) is not None,
            "historico": self.repo.historico_do_vendedor(vendedor_id),
        }

    # --- comprovantes -------------------------------------------------------

    def registrar_comprovante(
        self,
        vendedor_id: uuid.UUID,
        valor: float,
        arquivo_nome: str,
        arquivo_caminho: str,
        arquivo_tipo: str,
    ) -> PagamentoAssinatura:
        """RN-A04. Recusa um segundo envio enquanto houver um em análise."""
        if self.repo.pendente_do_vendedor(vendedor_id) is not None:
            raise ComprovanteJaPendente()
        return self.repo.criar_pagamento(
            PagamentoAssinatura(
                vendedor_id=vendedor_id,
                valor=valor,
                arquivo_nome=arquivo_nome,
                arquivo_caminho=arquivo_caminho,
                arquivo_tipo=arquivo_tipo,
                situacao="pendente",
            )
        )

    def aprovar(
        self, pagamento_id: uuid.UUID, admin_id: uuid.UUID, hoje: date | None = None
    ) -> PagamentoAssinatura:
        """RN-A02. Soma 30 dias a max(hoje, validade atual)."""
        hoje = hoje or date.today()
        pagamento = self._pendente(pagamento_id)

        nova = regras.renovar(self._vigencia(pagamento.vendedor_id), hoje)
        linha = self.repo.buscar(pagamento.vendedor_id)
        if linha is None:
            linha = Assinatura(vendedor_id=pagamento.vendedor_id, valido_ate=nova.valido_ate,
                               origem=nova.origem)
            self.repo.salvar(linha)
        else:
            linha.valido_ate = nova.valido_ate
            linha.origem = nova.origem

        pagamento.situacao = "aprovado"
        pagamento.avaliado_em = datetime.utcnow()
        pagamento.avaliado_por = admin_id
        self.repo.confirmar()
        return pagamento

    def recusar(
        self, pagamento_id: uuid.UUID, admin_id: uuid.UUID, motivo: str
    ) -> PagamentoAssinatura:
        """RN-A03. Recusar não mexe na vigência."""
        pagamento = self._pendente(pagamento_id)
        pagamento.situacao = "recusado"
        pagamento.avaliado_em = datetime.utcnow()
        pagamento.avaliado_por = admin_id
        pagamento.observacao = motivo
        self.repo.confirmar()
        return pagamento

    def pendentes(self) -> list[PagamentoAssinatura]:
        return self.repo.pendentes()

    def listar(self, situacao: str) -> list[PagamentoAssinatura]:
        """Fila (pendente) ou histórico (aprovado, recusado)."""
        return self.repo.por_situacao(situacao)

    def pagamento_por_id(self, pagamento_id: uuid.UUID) -> PagamentoAssinatura | None:
        return self.repo.pagamento_por_id(pagamento_id)

    def _pendente(self, pagamento_id: uuid.UUID) -> PagamentoAssinatura:
        pagamento = self.repo.pagamento_por_id(pagamento_id)
        if pagamento is None:
            raise ComprovanteNaoEncontrado()
        if pagamento.situacao != "pendente":
            raise ComprovanteJaAvaliado()
        return pagamento


class ComprovanteJaPendente(Exception):
    """Já existe um comprovante em análise para este vendedor (RN-A04)."""


class ComprovanteNaoEncontrado(Exception):
    """O comprovante informado não existe."""


class ComprovanteJaAvaliado(Exception):
    """O comprovante já foi aprovado ou recusado."""
