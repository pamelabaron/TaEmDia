"""Monta o dashboard financeiro a partir das consultas agregadas."""
import uuid
from datetime import date

from app.modules.relatorios.repository import RelatorioRepository


def _primeiro_dia_meses_atras(d: date, n: int) -> date:
    """Primeiro dia do mês n meses atrás (n=5 => janela de 6 meses incluindo o atual)."""
    total = d.month - 1 - n
    ano = d.year + total // 12
    mes = total % 12 + 1
    return date(ano, mes, 1)


class RelatorioService:
    def __init__(self, repo: RelatorioRepository):
        self.repo = repo

    def dashboard(self, vendedor_id: uuid.UUID) -> dict:
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        desde = _primeiro_dia_meses_atras(hoje, 5)

        mensais = self.repo.recebimentos_mensais(vendedor_id, desde)
        atrasados = self.repo.clientes_em_atraso(vendedor_id, hoje)

        return {
            "total_a_receber": float(self.repo.total_a_receber(vendedor_id)),
            "recebido_no_mes": float(self.repo.recebido_no_mes(vendedor_id, inicio_mes)),
            "em_atraso": float(self.repo.em_atraso(vendedor_id, hoje)),
            "clientes_inadimplentes": self.repo.clientes_inadimplentes(vendedor_id, hoje),
            "recebimentos_mensais": [{"mes": m, "total": float(v)} for m, v in mensais],
            "clientes_em_atraso": [
                {"id": cid, "nome": nome, "valor_atrasado": float(valor)}
                for cid, nome, valor in atrasados
            ],
        }
