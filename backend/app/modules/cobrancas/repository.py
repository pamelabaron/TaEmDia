"""Acesso ao banco do log de cobranças e das respostas dos devedores."""
import uuid
from datetime import date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.clientes.models import Cliente
from app.modules.cobrancas.models import CobrancaLog, RespostaDevedor
from app.modules.vendas.models import Parcela, Venda


class CobrancaLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def registrar(self, log: CobrancaLog) -> CobrancaLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def salvar(self) -> None:
        self.db.commit()

    def contar_do_dia(self, vendedor_id: uuid.UUID, cliente_id: uuid.UUID, dia: date) -> int:
        """Quantas mensagens automáticas já foram enviadas hoje para este cliente (RN10)."""
        inicio = datetime.combine(dia, time.min)
        fim = datetime.combine(dia, time.max)
        stmt = (
            select(func.count(CobrancaLog.id))
            .where(
                CobrancaLog.vendedor_id == vendedor_id,
                CobrancaLog.cliente_id == cliente_id,
                CobrancaLog.status == "enviado",
                CobrancaLog.tipo != "resumo",
                CobrancaLog.criado_em.between(inicio, fim),
            )
        )
        return self.db.scalar(stmt) or 0

    def listar(
        self, vendedor_id: uuid.UUID, desde: date | None = None, limite: int = 200
    ) -> list[tuple[CobrancaLog, str]]:
        """Log com o nome do cliente, mais recentes primeiro."""
        stmt = (
            select(CobrancaLog, Cliente.nome)
            .outerjoin(Cliente, CobrancaLog.cliente_id == Cliente.id)
            .where(CobrancaLog.vendedor_id == vendedor_id)
            .order_by(CobrancaLog.criado_em.desc())
            .limit(limite)
        )
        if desde is not None:
            stmt = stmt.where(CobrancaLog.criado_em >= datetime.combine(desde, time.min))
        return [(linha[0], linha[1] or "Você") for linha in self.db.execute(stmt)]

    def pendentes_de_reenvio(self, limite: int = 50) -> list[CobrancaLog]:
        """Mensagens que ficaram na fila por falha de conexão (FE01)."""
        stmt = (
            select(CobrancaLog)
            .where(CobrancaLog.status == "pendente")
            .order_by(CobrancaLog.criado_em)
            .limit(limite)
        )
        return list(self.db.scalars(stmt))


class RespostaRepository:
    def __init__(self, db: Session):
        self.db = db

    def registrar(self, resposta: RespostaDevedor) -> RespostaDevedor:
        self.db.add(resposta)
        self.db.commit()
        self.db.refresh(resposta)
        return resposta

    def ja_registrada(self, parcela_id: uuid.UUID, opcao: str) -> bool:
        """Evita processar a mesma opção duas vezes para a mesma parcela (RN12/FE04)."""
        stmt = select(func.count(RespostaDevedor.id)).where(
            RespostaDevedor.parcela_id == parcela_id,
            RespostaDevedor.opcao == opcao,
        )
        return (self.db.scalar(stmt) or 0) > 0

    def do_dia(self, vendedor_id: uuid.UUID, dia: date) -> list[RespostaDevedor]:
        inicio = datetime.combine(dia, time.min)
        fim = datetime.combine(dia, time.max)
        stmt = select(RespostaDevedor).where(
            RespostaDevedor.vendedor_id == vendedor_id,
            RespostaDevedor.recebido_em.between(inicio, fim),
        )
        return list(self.db.scalars(stmt))


class CobrancaParcelaRepository:
    """Consultas de parcelas usadas pelo motor de cobrança."""

    def __init__(self, db: Session):
        self.db = db

    def elegiveis(self, hoje: date, ate: date) -> list[tuple[Parcela, Venda, Cliente]]:
        """Parcelas em aberto de vendas ativas que vencem até 'ate' (inclui atrasadas),
        de clientes ativos e com envio automático habilitado."""
        stmt = (
            select(Parcela, Venda, Cliente)
            .join(Venda, Parcela.venda_id == Venda.id)
            .join(Cliente, Venda.cliente_id == Cliente.id)
            .where(
                Venda.status == "ativa",
                Cliente.ativo.is_(True),
                Cliente.envio_auto_ativo.is_(True),
                Parcela.data_pagamento.is_(None),
                Parcela.data_vencimento <= ate,
            )
            .order_by(Parcela.data_vencimento)
        )
        return [(l[0], l[1], l[2]) for l in self.db.execute(stmt)]

    def por_id(self, vendedor_id: uuid.UUID, parcela_id: uuid.UUID) -> tuple[Parcela, Venda, Cliente] | None:
        stmt = (
            select(Parcela, Venda, Cliente)
            .join(Venda, Parcela.venda_id == Venda.id)
            .join(Cliente, Venda.cliente_id == Cliente.id)
            .where(Parcela.id == parcela_id, Venda.vendedor_id == vendedor_id)
        )
        linha = self.db.execute(stmt).first()
        return (linha[0], linha[1], linha[2]) if linha else None

    def aberta_mais_antiga_por_numero(
        self, numero: str
    ) -> tuple[Parcela, Venda, Cliente] | None:
        """Localiza o devedor pelo número e devolve a parcela em aberto mais antiga (RN14)."""
        stmt = (
            select(Parcela, Venda, Cliente)
            .join(Venda, Parcela.venda_id == Venda.id)
            .join(Cliente, Venda.cliente_id == Cliente.id)
            .where(
                Cliente.whatsapp_numero == numero,
                Cliente.ativo.is_(True),
                Venda.status == "ativa",
                Parcela.data_pagamento.is_(None),
            )
            .order_by(Parcela.data_vencimento)
            .limit(1)
        )
        linha = self.db.execute(stmt).first()
        return (linha[0], linha[1], linha[2]) if linha else None

    def pagas_no_dia(self, vendedor_id: uuid.UUID, dia: date) -> list[Parcela]:
        """Parcelas cujo pagamento foi confirmado no dia (para o resumo diário)."""
        stmt = (
            select(Parcela)
            .join(Venda, Parcela.venda_id == Venda.id)
            .where(Venda.vendedor_id == vendedor_id, Parcela.data_pagamento == dia)
        )
        return list(self.db.scalars(stmt))

    def salvar(self) -> None:
        self.db.commit()
