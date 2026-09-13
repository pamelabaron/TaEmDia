"""Acesso ao banco para assinatura e comprovantes.

Única camada que toca o banco — o serviço nunca consulta direto.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assinatura.models import Assinatura, PagamentoAssinatura


class AssinaturaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- vigência -----------------------------------------------------------

    def buscar(self, vendedor_id: uuid.UUID) -> Assinatura | None:
        return self.db.execute(
            select(Assinatura).where(Assinatura.vendedor_id == vendedor_id)
        ).scalar_one_or_none()

    def salvar(self, assinatura: Assinatura) -> Assinatura:
        self.db.add(assinatura)
        self.db.commit()
        self.db.refresh(assinatura)
        return assinatura

    # --- comprovantes -------------------------------------------------------

    def criar_pagamento(self, pagamento: PagamentoAssinatura) -> PagamentoAssinatura:
        self.db.add(pagamento)
        self.db.commit()
        self.db.refresh(pagamento)
        return pagamento

    def pagamento_por_id(self, pagamento_id: uuid.UUID) -> PagamentoAssinatura | None:
        return self.db.get(PagamentoAssinatura, pagamento_id)

    def pendente_do_vendedor(self, vendedor_id: uuid.UUID) -> PagamentoAssinatura | None:
        """RN-A04 — no máximo um comprovante pendente por vez."""
        return self.db.execute(
            select(PagamentoAssinatura).where(
                PagamentoAssinatura.vendedor_id == vendedor_id,
                PagamentoAssinatura.situacao == "pendente",
            )
        ).scalars().first()

    def historico_do_vendedor(self, vendedor_id: uuid.UUID) -> list[PagamentoAssinatura]:
        return list(
            self.db.execute(
                select(PagamentoAssinatura)
                .where(PagamentoAssinatura.vendedor_id == vendedor_id)
                .order_by(PagamentoAssinatura.enviado_em.desc())
            ).scalars()
        )

    def pendentes(self) -> list[PagamentoAssinatura]:
        """Fila de conferência da administradora, mais antigos primeiro."""
        return list(
            self.db.execute(
                select(PagamentoAssinatura)
                .where(PagamentoAssinatura.situacao == "pendente")
                .order_by(PagamentoAssinatura.enviado_em.asc())
            ).scalars()
        )

    def confirmar(self) -> None:
        self.db.commit()
