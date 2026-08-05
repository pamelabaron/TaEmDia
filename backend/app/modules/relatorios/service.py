"""Monta o dashboard financeiro a partir das consultas agregadas."""
import uuid
from collections import defaultdict
from datetime import date

from app.modules.clientes.repository import ClienteRepository
from app.modules.relatorios.ranking import ParcelaRanking, classificar
from app.modules.relatorios.repository import RelatorioRepository


def _primeiro_dia_meses_atras(d: date, n: int) -> date:
    """Primeiro dia do mês n meses atrás (n=5 => janela de 6 meses incluindo o atual)."""
    total = d.month - 1 - n
    ano = d.year + total // 12
    mes = total % 12 + 1
    return date(ano, mes, 1)


CATEGORIAS_ORDEM = {"inadimplente": 0, "regular": 1, "bom": 2, "sem_historico": 3}


class RelatorioService:
    def __init__(self, repo: RelatorioRepository, cliente_repo: ClienteRepository):
        self.repo = repo
        self.cliente_repo = cliente_repo

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

    def ranking(self, vendedor_id: uuid.UUID, meses: int = 12) -> dict:
        hoje = date.today()
        desde = _primeiro_dia_meses_atras(hoje, meses - 1)

        # Agrupa as parcelas do período por cliente.
        por_cliente: dict = defaultdict(list)
        for cliente_id, venc, pago in self.repo.parcelas_para_ranking(vendedor_id, desde):
            por_cliente[cliente_id].append(ParcelaRanking(venc, pago))

        clientes_out = []
        contagem = {"bom": 0, "regular": 0, "inadimplente": 0, "sem_historico": 0}
        for cliente in self.cliente_repo.listar(vendedor_id):
            c = classificar(por_cliente.get(cliente.id, []), hoje)
            contagem[c.categoria] += 1
            clientes_out.append({
                "id": cliente.id,
                "nome": cliente.nome,
                "classificacao": c.categoria,
                "percentual_em_dia": c.percentual_em_dia,
                "media_dias_atraso": c.media_dias_atraso,
                "total_avaliadas": c.total_avaliadas,
            })

        # Ordena: inadimplentes primeiro (atenção), depois regulares, bons e sem histórico.
        clientes_out.sort(key=lambda x: (CATEGORIAS_ORDEM[x["classificacao"]], -x["percentual_em_dia"]))

        return {
            "bons": contagem["bom"],
            "regulares": contagem["regular"],
            "inadimplentes": contagem["inadimplente"],
            "sem_historico": contagem["sem_historico"],
            "clientes": clientes_out,
        }
