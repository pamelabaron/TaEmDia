"""O nome que a pessoa deu ao arquivo é texto de fora, e precisa ser limpo.

O arquivo em disco já nasce seguro: o nome dele é um UUID gerado aqui, e o que
a pessoa digitou nunca entra na formação do caminho. Isso não está em questão.

O que está é o **outro** nome, o original, que é guardado no banco só para a
administradora ver "nota-fiscal.pdf" em vez de um UUID. Esse valor:

- vai para o cabeçalho `Content-Disposition` no download;
- é gravado numa coluna de texto sem limite;
- vem inteiro do cliente HTTP, que pode mandar o que quiser.

Nenhuma dessas três coisas é falha por si só. O Starlette codifica o cabeçalho
(testado: `\\r\\n` sai como `%0D%0A`, não injeta nada) e a rota de download
exige administradora. Mas guardar `../../etc/passwd` ou 40 mil caracteres num
campo que ninguém limita é sujeira que não custa nada evitar, e que fica difícil
de limpar depois que houver dado de verdade.

A regra: fica só o nome do arquivo, sem caminho, sem caractere de controle,
com tamanho de gente. Nunca vazio.
"""
import pytest

from app.modules.assinatura.armazenamento import NOME_MAXIMO, NOME_PADRAO, nome_seguro


class TestTiraOCaminho:
    """Barra e contrabarra somem: o que sobra é o nome do arquivo."""

    @pytest.mark.parametrize("entrada, esperado", [
        ("../../etc/passwd", "passwd"),
        ("/etc/shadow", "shadow"),
        ("..\\..\\windows\\system32\\config", "config"),
        ("pasta/subpasta/nota.pdf", "nota.pdf"),
        ("C:\\Users\\Ana\\Documentos\\pix.png", "pix.png"),
    ])
    def test_sobra_so_o_nome(self, entrada, esperado):
        assert nome_seguro(entrada) == esperado

    def test_nome_que_e_so_pontos_vira_o_padrao(self):
        """"..", sozinho, não é nome de arquivo nenhum."""
        assert nome_seguro("..") == NOME_PADRAO
        assert nome_seguro(".") == NOME_PADRAO
        assert nome_seguro("../../") == NOME_PADRAO


class TestTiraCaractereDeControle:
    """Quebra de linha e afins não têm o que fazer num nome de arquivo."""

    def test_quebra_de_linha_some(self):
        assert "\n" not in nome_seguro("quebra\nlinha.png")
        assert "\r" not in nome_seguro("quebra\r\nX-Injetado: sim.png")

    def test_tabulacao_e_nulo_somem(self):
        limpo = nome_seguro("com\ttab\x00e nulo.png")
        assert "\t" not in limpo and "\x00" not in limpo

    def test_o_resto_do_nome_sobrevive(self):
        """Limpar não é destruir: o que era legível continua legível."""
        assert nome_seguro("quebra\nlinha.png") == "quebralinha.png"


class TestTamanho:
    def test_nome_enorme_e_cortado(self):
        enorme = "a" * 5000 + ".pdf"
        assert len(nome_seguro(enorme)) <= NOME_MAXIMO

    def test_o_corte_preserva_a_extensao(self):
        """A extensão é o que diz à administradora o que ela vai abrir."""
        assert nome_seguro("a" * 5000 + ".pdf").endswith(".pdf")

    def test_nome_normal_nao_e_mexido(self):
        assert nome_seguro("comprovante-outubro.pdf") == "comprovante-outubro.pdf"

    def test_acento_e_espaco_continuam_valendo(self):
        """Não é higienização agressiva: nome em português é nome legítimo."""
        assert nome_seguro("comprovante de março.png") == "comprovante de março.png"


class TestNuncaVazio:
    """A coluna é obrigatória no banco. Devolver vazio quebraria a gravação."""

    @pytest.mark.parametrize("entrada", [None, "", "   ", "\n\n", "///"])
    def test_vira_o_padrao(self, entrada):
        assert nome_seguro(entrada) == NOME_PADRAO


class TestNoCaminhoDeVerdade:
    """A limpeza precisa estar ligada no endpoint, não só existir."""

    def test_o_envio_guarda_o_nome_limpo(self, cliente_http, cabecalho_vencido):
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
        resposta = cliente_http.post(
            "/assinatura/comprovante",
            data={"valor": "19.90"},
            files={"arquivo": ("../../etc/passwd.png", png, "image/png")},
            headers=cabecalho_vencido,
        )
        assert resposta.status_code == 201, resposta.text
        assert resposta.json()["arquivo_nome"] == "passwd.png"
