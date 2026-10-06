"""Regras de CPF e de telefone do cliente (RN-C01 e RN-C02).

Por que estas regras existem: o sistema só cumpre sua função se a mensagem
chegar. O número guardado vai direto para o WhatsApp, e lá ele precisa do
código do país. Antes desta validação, um cliente estava salvo como
"4799..." em vez de "554799...", e qualquer cobrança para ele se perderia
sem ninguém perceber. O aviso só chegaria pela boca do vendedor, meses
depois, na forma de "o cliente disse que nunca recebeu nada".

O CPF segue a mesma lógica: campo sem conferência aceita "abc" e aceita
"111.111.111-11", e aí o dado existe mas não identifica ninguém.
"""
import pytest

from app.modules.clientes.regras import (
    DDDS_VALIDOS,
    formatar_telefone,
    normalizar_cpf,
    normalizar_telefone,
)


class TestTelefone:
    """RN-C01. O número é guardado como código do país, DDD e número."""

    @pytest.mark.parametrize(
        "digitado",
        [
            "47999990000",
            "(47) 99999-0000",
            "47 99999-0000",
            "  47999990000  ",
            "5547999990000",
            "+55 (47) 99999-0000",
            "55 47 99999 0000",
        ],
    )
    def test_mesmo_numero_escrito_de_varios_jeitos(self, digitado):
        """Ninguém digita telefone do mesmo jeito. Todos viram o mesmo dado."""
        assert normalizar_telefone(digitado) == "5547999990000"

    def test_telefone_fixo_de_oito_digitos_e_aceito(self):
        """Existe WhatsApp Business em telefone fixo."""
        assert normalizar_telefone("47 3333-0000") == "554733330000"

    def test_sem_ddd_e_recusado(self):
        """Decisão da autora: pedir o DDD, nunca adivinhar.

        Adivinhar mandaria a cobrança para outra pessoa, na outra ponta do
        país, e o erro só apareceria quando alguém reclamasse.
        """
        with pytest.raises(ValueError, match="DDD"):
            normalizar_telefone("999990000")

    @pytest.mark.parametrize("ddd", ["10", "20", "23", "30", "40", "50", "60", "70", "80", "90"])
    def test_ddd_que_nao_existe_e_recusado(self, ddd):
        """Erro de digitação no DDD costuma cair num código inexistente."""
        with pytest.raises(ValueError, match="DDD"):
            normalizar_telefone(f"{ddd}999990000")

    def test_a_lista_de_ddds_cobre_o_pais(self):
        """Sanidade da lista: 67 DDDs em uso no Brasil."""
        assert len(DDDS_VALIDOS) == 67
        for ddd in ("11", "47", "48", "61", "71", "85", "92", "99"):
            assert ddd in DDDS_VALIDOS

    @pytest.mark.parametrize(
        "digitado, motivo",
        [
            ("4799999", "curto demais"),
            ("479999900001234", "longo demais"),
            ("", "vazio"),
            ("   ", "só espaço"),
            ("abcdefghijk", "sem nenhum dígito"),
        ],
    )
    def test_tamanho_impossivel_e_recusado(self, digitado, motivo):
        with pytest.raises(ValueError):
            normalizar_telefone(digitado)

    def test_celular_de_nove_digitos_comeca_com_nove(self):
        """Número de nove dígitos que não começa com 9 é dígito sobrando."""
        with pytest.raises(ValueError):
            normalizar_telefone("47 89999-0000")

    def test_outro_pais_e_aceito_quando_informado(self):
        """O 55 é o padrão, não uma prisão. Vendedor com cliente fora do país."""
        assert normalizar_telefone("351 912 345 678", codigo_pais="351") == "351912345678"

    def test_codigo_do_pais_repetido_nao_duplica(self):
        """Digitar o 55 no campo do número, com 55 já no campo do país."""
        assert normalizar_telefone("5547999990000", codigo_pais="55") == "5547999990000"

    def test_codigo_de_pais_invalido_e_recusado(self):
        with pytest.raises(ValueError, match="[Cc]ódigo do país"):
            normalizar_telefone("47999990000", codigo_pais="abc")


class TestExibicaoDoTelefone:
    """Guardado é só dígito; na tela a pessoa lê como está acostumada."""

    def test_celular_brasileiro(self):
        assert formatar_telefone("5547999990000") == "55 (47) 99999-0000"

    def test_fixo_brasileiro(self):
        assert formatar_telefone("554733330000") == "55 (47) 3333-0000"

    def test_numero_de_fora_nao_ganha_formato_brasileiro(self):
        """Só o "+" na frente: o dado guardado não diz onde o código do país
        termina, e separar no lugar errado confundiria mais que ajudar."""
        assert formatar_telefone("351912345678") == "+351912345678"

    def test_valor_estranho_volta_como_veio(self):
        """Formatar é enfeite. Nunca pode quebrar a tela por causa de dado velho."""
        assert formatar_telefone("") == ""
        assert formatar_telefone("123") == "123"


class TestCpf:
    """RN-C02. CPF é opcional, mas quando existe precisa ser um CPF."""

    def test_guarda_so_os_digitos(self):
        assert normalizar_cpf("529.982.247-25") == "52998224725"

    def test_aceita_ja_sem_pontuacao(self):
        assert normalizar_cpf("52998224725") == "52998224725"

    @pytest.mark.parametrize("vazio", [None, "", "   "])
    def test_campo_vazio_continua_valendo(self, vazio):
        """O CPF é opcional (RF04). Não preencher não é erro."""
        assert normalizar_cpf(vazio) is None

    @pytest.mark.parametrize(
        "quantidade, cpf",
        [(10, "5299822472"), (12, "529982247251"), (3, "529")],
    )
    def test_quantidade_de_digitos_diferente_de_onze_e_recusada(self, quantidade, cpf):
        assert len(cpf.replace(".", "").replace("-", "")) == quantidade
        with pytest.raises(ValueError, match="11"):
            normalizar_cpf(cpf)

    @pytest.mark.parametrize(
        "repetido",
        ["00000000000", "11111111111", "55555555555", "99999999999"],
    )
    def test_todos_os_digitos_iguais_e_recusado(self, repetido):
        """Passa na conta do tamanho, mas não é CPF de ninguém.

        É o que as pessoas digitam para vencer campo obrigatório chato.
        """
        with pytest.raises(ValueError):
            normalizar_cpf(repetido)

    @pytest.mark.parametrize(
        "errado",
        ["52998224726", "52998224715", "11144477736", "12345678909"[:-1] + "0"],
    )
    def test_digito_verificador_errado_e_recusado(self, errado):
        """É o que separa um CPF de onze números quaisquer."""
        with pytest.raises(ValueError, match="CPF"):
            normalizar_cpf(errado)

    @pytest.mark.parametrize("valido", ["52998224725", "11144477735", "12345678909"])
    def test_cpf_valido_passa(self, valido):
        assert normalizar_cpf(valido) == valido

    def test_letra_no_meio_e_recusada(self):
        with pytest.raises(ValueError):
            normalizar_cpf("529.98a.247-25")
