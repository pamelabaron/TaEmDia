"""Geração do relatório financeiro em PDF (WeasyPrint, a partir de HTML/CSS)."""
from datetime import date
from html import escape

ESTILO = """
  @page { size: A4; margin: 1.6cm; }
  body { font-family: Helvetica, Arial, sans-serif; color: #222; font-size: 11px; }
  h1 { color: #1565c0; font-size: 20px; margin: 0 0 2px; }
  .periodo { color: #666; margin-bottom: 4px; }
  .vendedor { color: #666; margin-bottom: 16px; }
  .kpis { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
  .kpis td { border: 1px solid #ddd; padding: 10px; width: 25%; text-align: center; }
  .kpis .rotulo { display: block; color: #777; font-size: 9px; text-transform: uppercase; }
  .kpis .valor { display: block; font-size: 15px; font-weight: bold; margin-top: 4px; }
  h2 { font-size: 13px; margin: 18px 0 6px; color: #333; }
  table.dados { width: 100%; border-collapse: collapse; }
  table.dados th { background: #f0f4f8; text-align: left; padding: 6px; font-size: 10px;
                   border-bottom: 2px solid #d0d8e0; }
  table.dados td { padding: 6px; border-bottom: 1px solid #eee; }
  table.dados tr:nth-child(even) td { background: #fafafa; }
  .num { text-align: right; }
  .paga { color: #2e7d32; } .atrasada { color: #c62828; } .pendente { color: #1565c0; }
  .vazio { color: #888; font-style: italic; padding: 10px 0; }
  .rodape { position: fixed; bottom: -0.9cm; width: 100%; text-align: center;
            color: #999; font-size: 9px; }
"""


def _dinheiro(valor) -> str:
    return "R$ " + f"{float(valor):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _data(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else "-"


def _status(vencimento: date, pagamento: date | None, hoje: date) -> str:
    if pagamento is not None:
        return "paga"
    return "atrasada" if vencimento < hoje else "pendente"


def montar_html(
    vendedor_nome: str,
    desde: date,
    ate: date,
    kpis: dict,
    parcelas: list[tuple],
    hoje: date | None = None,
) -> str:
    """Monta o HTML do relatório. Separado da geração do PDF para facilitar os testes."""
    hoje = hoje or date.today()
    rotulos = {"paga": "Paga", "atrasada": "Atrasada", "pendente": "Pendente"}

    linhas = []
    total_periodo = 0.0
    total_recebido = 0.0
    for nome, numero, valor, vencimento, pagamento in parcelas:
        st = _status(vencimento, pagamento, hoje)
        total_periodo += float(valor)
        if st == "paga":
            total_recebido += float(valor)
        linhas.append(
            f"<tr><td>{escape(str(nome))}</td>"
            f"<td class='num'>{numero}</td>"
            f"<td class='num'>{_dinheiro(valor)}</td>"
            f"<td>{_data(vencimento)}</td>"
            f"<td class='{st}'>{rotulos[st]}</td>"
            f"<td>{_data(pagamento)}</td></tr>"
        )

    if linhas:
        corpo = (
            "<table class='dados'>"
            "<tr><th>Cliente</th><th class='num'>Parcela</th><th class='num'>Valor</th>"
            "<th>Vencimento</th><th>Situação</th><th>Pagamento</th></tr>"
            + "".join(linhas)
            + f"<tr><td colspan='2'><strong>Total do período</strong></td>"
              f"<td class='num'><strong>{_dinheiro(total_periodo)}</strong></td>"
              f"<td colspan='2'>Recebido</td>"
              f"<td class='num'><strong>{_dinheiro(total_recebido)}</strong></td></tr>"
            + "</table>"
        )
    else:
        corpo = "<p class='vazio'>Nenhuma parcela com vencimento neste período.</p>"

    inadimplentes = kpis.get("clientes_em_atraso") or []
    if inadimplentes:
        itens = "".join(
            f"<tr><td>{escape(str(c['nome']))}</td>"
            f"<td class='num atrasada'>{_dinheiro(c['valor_atrasado'])}</td></tr>"
            for c in inadimplentes
        )
        bloco_atraso = (
            "<h2>Clientes em atraso</h2>"
            "<table class='dados'><tr><th>Cliente</th><th class='num'>Valor em aberto</th></tr>"
            + itens + "</table>"
        )
    else:
        bloco_atraso = "<h2>Clientes em atraso</h2><p class='vazio'>Nenhum cliente em atraso.</p>"

    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><style>{ESTILO}</style></head>
<body>
  <h1>TáEmDia. Relatório Financeiro</h1>
  <div class="periodo">Período: {_data(desde)} a {_data(ate)}</div>
  <div class="vendedor">{escape(str(vendedor_nome))} · emitido em {_data(hoje)}</div>

  <table class="kpis"><tr>
    <td><span class="rotulo">Total a receber</span>
        <span class="valor">{_dinheiro(kpis.get('total_a_receber', 0))}</span></td>
    <td><span class="rotulo">Recebido no mês</span>
        <span class="valor">{_dinheiro(kpis.get('recebido_no_mes', 0))}</span></td>
    <td><span class="rotulo">Em atraso</span>
        <span class="valor">{_dinheiro(kpis.get('em_atraso', 0))}</span></td>
    <td><span class="rotulo">Inadimplentes</span>
        <span class="valor">{kpis.get('clientes_inadimplentes', 0)}</span></td>
  </tr></table>

  <h2>Parcelas do período</h2>
  {corpo}
  {bloco_atraso}
  <div class="rodape">TáEmDia · relatório gerado automaticamente</div>
</body></html>"""


def gerar_pdf(html: str) -> bytes:
    """Converte o HTML do relatório em PDF."""
    from weasyprint import HTML  # importado aqui para não pesar o start da aplicação

    return HTML(string=html).write_pdf()
