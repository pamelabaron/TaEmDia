"""Testes do relatório financeiro exportado em PDF."""
from datetime import date, timedelta

import pytest

from app.modules.relatorios.pdf import _dinheiro, _status, montar_html

HOJE = date(2026, 8, 26)

KPIS = {
    "total_a_receber": 450.0,
    "recebido_no_mes": 150.0,
    "em_atraso": 300.0,
    "clientes_inadimplentes": 1,
    "clientes_em_atraso": [{"nome": "Rosangela Ferreira", "valor_atrasado": 300.0}],
}

PARCELAS = [
    ("Rosangela Ferreira", 1, 150.0, date(2026, 7, 10), None),
    ("Rosangela Ferreira", 2, 150.0, date(2026, 8, 10), date(2026, 8, 12)),
    ("Rosangela Ferreira", 3, 150.0, date(2026, 9, 10), None),
]


class TestFormatacao:
    @pytest.mark.parametrize(
        "valor,esperado",
        [(0, "R$ 0,00"), (150.5, "R$ 150,50"), (1234.56, "R$ 1.234,56"),
         (1000000, "R$ 1.000.000,00")],
    )
    def test_dinheiro_no_padrao_brasileiro(self, valor, esperado):
        assert _dinheiro(valor) == esperado

    def test_status_paga(self):
        assert _status(date(2026, 8, 1), date(2026, 8, 5), HOJE) == "paga"

    def test_status_atrasada(self):
        assert _status(date(2026, 8, 1), None, HOJE) == "atrasada"

    def test_status_pendente(self):
        assert _status(date(2026, 9, 1), None, HOJE) == "pendente"


class TestConteudoDoRelatorio:
    def _html(self, parcelas=None, kpis=None):
        return montar_html(
            "Pâmela Baron", date(2026, 7, 1), date(2026, 12, 31),
            kpis if kpis is not None else KPIS,
            parcelas if parcelas is not None else PARCELAS,
            hoje=HOJE,
        )

    def test_cabecalho_com_periodo_e_vendedor(self):
        html = self._html()
        assert "Relatório Financeiro" in html
        assert "01/07/2026" in html and "31/12/2026" in html
        assert "Pâmela Baron" in html

    def test_mostra_os_quatro_indicadores(self):
        html = self._html()
        assert "R$ 450,00" in html   # total a receber
        assert "R$ 150,00" in html   # recebido no mês
        assert "R$ 300,00" in html   # em atraso
        assert "Inadimplentes" in html

    def test_lista_todas_as_parcelas(self):
        html = self._html()
        assert html.count("Rosangela Ferreira") >= 3
        assert "10/07/2026" in html and "10/08/2026" in html and "10/09/2026" in html

    def test_classifica_cada_parcela(self):
        html = self._html()
        assert "Atrasada" in html   # vencida em 10/07 sem pagamento
        assert "Paga" in html       # paga em 12/08
        assert "Pendente" in html   # vence em 10/09

    def test_totaliza_o_periodo(self):
        """3 parcelas de 150 = 450 no período, das quais 150 recebidas."""
        html = self._html()
        assert "Total do período" in html
        assert "R$ 450,00" in html

    def test_bloco_de_clientes_em_atraso(self):
        html = self._html()
        assert "Clientes em atraso" in html
        assert "Rosangela Ferreira" in html

    def test_periodo_sem_parcelas(self):
        html = self._html(parcelas=[])
        assert "Nenhuma parcela com vencimento neste período" in html

    def test_sem_inadimplentes(self):
        kpis = {**KPIS, "clientes_em_atraso": [], "clientes_inadimplentes": 0}
        html = self._html(kpis=kpis)
        assert "Nenhum cliente em atraso" in html

    def test_escapa_caracteres_perigosos_no_nome(self):
        """Um nome com HTML não pode quebrar nem injetar conteúdo no relatório."""
        parcelas = [("<script>alerta</script>", 1, 100.0, date(2026, 8, 1), None)]
        html = self._html(parcelas=parcelas)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_html_e_bem_formado(self):
        html = self._html()
        assert html.startswith("<!DOCTYPE html>")
        assert html.rstrip().endswith("</html>")


class TestApiPdf:
    def test_exige_autenticacao(self, cliente_http):
        assert cliente_http.get("/relatorios/pdf").status_code == 401

    def test_gera_um_pdf_valido(self, cliente_http, cabecalho_auth):
        resp = cliente_http.get("/relatorios/pdf", headers=cabecalho_auth)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF")

    def test_sugere_nome_de_arquivo_para_download(self, cliente_http, cabecalho_auth):
        resp = cliente_http.get("/relatorios/pdf", headers=cabecalho_auth)
        assert "attachment" in resp.headers["content-disposition"]
        assert ".pdf" in resp.headers["content-disposition"]

    def test_aceita_filtro_de_periodo(self, cliente_http, cabecalho_auth):
        resp = cliente_http.get("/relatorios/pdf?desde=2026-01-01&ate=2026-12-31",
                                headers=cabecalho_auth)
        assert resp.status_code == 200
        assert "20260101-20261231" in resp.headers["content-disposition"]

    def test_inclui_as_parcelas_do_periodo(self, cliente_http, cabecalho_auth):
        cid = cliente_http.post("/clientes", headers=cabecalho_auth,
                                json={"nome": "Ana", "whatsapp_numero": "5547999990022"}).json()["id"]
        cliente_http.post("/vendas", headers=cabecalho_auth, json={
            "cliente_id": cid, "valor_total": 300, "num_parcelas": 2,
            "data_primeira_parcela": str(date.today()),
        })
        resp = cliente_http.get(
            f"/relatorios/pdf?desde={date.today()}&ate={date.today() + timedelta(days=60)}",
            headers=cabecalho_auth,
        )
        assert resp.status_code == 200
        assert len(resp.content) > 1000
