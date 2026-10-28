"""Testes da substituição de variáveis nos templates de mensagem."""
import pytest

from app.modules.templates.service import EXEMPLO, TEMPLATES_PADRAO, VARIAVEIS, renderizar


class TestRenderizacao:
    def test_substitui_uma_variavel(self):
        assert renderizar("Olá {nome_cliente}!", {"nome_cliente": "Ana"}) == "Olá Ana!"

    def test_substitui_varias_variaveis(self):
        texto = renderizar(
            "{nome_cliente} deve {valor_parcela} desde {data_vencimento}",
            {"nome_cliente": "Ana", "valor_parcela": "R$ 50,00", "data_vencimento": "01/08/2026"},
        )
        assert texto == "Ana deve R$ 50,00 desde 01/08/2026"

    def test_repete_a_substituicao_em_todas_as_ocorrencias(self):
        assert renderizar("{nome_cliente}, {nome_cliente}!", {"nome_cliente": "Ana"}) == "Ana, Ana!"

    def test_variavel_sem_valor_permanece_no_texto(self):
        """Não quebra a mensagem se faltar um dado."""
        assert renderizar("Olá {nome_cliente} {dias_atraso}", {"nome_cliente": "Ana"}) == "Olá Ana {dias_atraso}"

    def test_variavel_desconhecida_e_ignorada(self):
        assert renderizar("Olá {inexistente}", {"inexistente": "x"}) == "Olá {inexistente}"

    def test_texto_sem_variaveis_nao_muda(self):
        assert renderizar("Bom dia!", EXEMPLO) == "Bom dia!"

    def test_converte_valores_nao_textuais(self):
        assert renderizar("{dias_atraso} dias", {"dias_atraso": 7}) == "7 dias"


class TestTemplatesPadrao:
    def test_existem_os_tres_tipos_do_rfc(self):
        assert set(TEMPLATES_PADRAO) == {"lembrete", "vencimento", "atraso"}

    @pytest.mark.parametrize("tipo", ["lembrete", "vencimento", "atraso"])
    def test_cada_padrao_tem_titulo_e_corpo(self, tipo):
        assert TEMPLATES_PADRAO[tipo]["titulo"]
        assert TEMPLATES_PADRAO[tipo]["corpo"]

    @pytest.mark.parametrize("tipo", ["lembrete", "vencimento", "atraso"])
    def test_padroes_usam_variaveis_e_renderizam_sem_sobras(self, tipo):
        corpo = TEMPLATES_PADRAO[tipo]["corpo"]
        assert "{nome_cliente}" in corpo
        renderizado = renderizar(corpo, EXEMPLO)
        assert "{" not in renderizado

    def test_lista_de_variaveis_documentada(self):
        assert VARIAVEIS == ["nome_cliente", "valor_parcela", "data_vencimento", "dias_atraso"]
