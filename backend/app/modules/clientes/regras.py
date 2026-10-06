"""Regras de CPF e telefone do cliente (RN-C01 e RN-C02).

Funções puras: recebem texto, devolvem texto ou levantam erro. Não tocam no
banco nem sabem que existe uma tela. Assim a mesma regra serve ao cadastro,
à edição e a qualquer importação futura, sem ninguém reescrever a conta.

Por que a regra vive aqui e não só no formulário: a tela pode ser contornada
por quem chamar a API direto. A tela avisa; esta camada decide.
"""
import re

#: Código do país que aparece primeiro no formulário. Decisão da autora:
#: o campo é editável, mas nasce com o Brasil preenchido.
CODIGO_PAIS_PADRAO = "55"

#: Os 67 DDDs em uso no Brasil. A lista existe porque a faixa de 11 a 99 tem
#: buracos (não existe DDD 20, 23, 30, 40, 50, 60, 70, 80, 90...), e erro de
#: digitação costuma cair justamente num deles.
DDDS_VALIDOS = frozenset(
    [
        "11", "12", "13", "14", "15", "16", "17", "18", "19",           # SP
        "21", "22", "24",                                               # RJ
        "27", "28",                                                     # ES
        "31", "32", "33", "34", "35", "37", "38",                       # MG
        "41", "42", "43", "44", "45", "46",                             # PR
        "47", "48", "49",                                               # SC
        "51", "53", "54", "55",                                         # RS
        "61",                                                           # DF
        "62", "64",                                                     # GO
        "63",                                                           # TO
        "65", "66",                                                     # MT
        "67",                                                           # MS
        "68",                                                           # AC
        "69",                                                           # RO
        "71", "73", "74", "75", "77",                                   # BA
        "79",                                                           # SE
        "81", "87",                                                     # PE
        "82",                                                           # AL
        "83",                                                           # PB
        "84",                                                           # RN
        "85", "88",                                                     # CE
        "86", "89",                                                     # PI
        "91", "93", "94",                                               # PA
        "92", "97",                                                     # AM
        "95",                                                           # RR
        "96",                                                           # AP
        "98", "99",                                                     # MA
    ]
)

#: Quantos dígitos o número tem depois do DDD. Nove é celular, oito é fixo.
#: O fixo continua aceito porque existe WhatsApp Business em linha fixa.
TAMANHOS_BRASIL = (8, 9)

#: Limite do padrão internacional E.164, contando o código do país.
MAXIMO_INTERNACIONAL = 15
MINIMO_INTERNACIONAL = 8

DIGITOS_DO_CPF = 11

#: Tamanho do nome. O nome mais longo já registrado no Brasil tem 90 letras;
#: o mínimo de 2 recusa o "X" que as pessoas digitam para pular o campo.
NOME_MINIMO = 2
NOME_MAXIMO = 120

#: Cabe rua, número, complemento, bairro e cidade numa linha só.
ENDERECO_MAXIMO = 200


def so_digitos(texto: str | None) -> str:
    """Joga fora ponto, traço, parênteses, espaço e o sinal de mais."""
    return re.sub(r"\D", "", texto or "")


def _limpar_codigo_pais(codigo_pais: str | None) -> str:
    """Campo em branco vira 55. Campo preenchido com bobagem é erro.

    A diferença importa: não preencher é o caso comum e o Brasil é o padrão,
    mas cair no padrão por causa de um valor que ninguém entendeu mandaria a
    cobrança para o país errado, calada.
    """
    bruto = (codigo_pais or "").strip()
    if not bruto:
        return CODIGO_PAIS_PADRAO

    pais = so_digitos(bruto)
    if not pais or len(pais) > 3:
        raise ValueError("Código do país inválido. Use de 1 a 3 dígitos, como 55.")
    return pais


def _tirar_codigo_repetido(digitos: str, pais: str) -> str:
    """Remove o código do país quando a pessoa o digitou junto do número.

    O corte olha o que sobra, não só o começo. Sem isso, o DDD 55 (Rio Grande
    do Sul) seria confundido com o código do Brasil e o número perderia dois
    dígitos: "55 99999-0000" viraria "99999-0000", sem DDD.
    """
    if not digitos.startswith(pais):
        return digitos

    resto = digitos[len(pais):]
    if pais == CODIGO_PAIS_PADRAO:
        cabe_como_nacional = len(resto) - 2 in TAMANHOS_BRASIL
    else:
        cabe_como_nacional = len(resto) >= 6

    return resto if cabe_como_nacional else digitos


def normalizar_telefone(numero: str | None, codigo_pais: str = CODIGO_PAIS_PADRAO) -> str:
    """Devolve o número pronto para o WhatsApp: código do país, DDD e número.

    O WhatsApp exige o código do país. Guardar sem ele faz a cobrança sair do
    sistema e não chegar em ninguém, sem nenhum erro aparecer no caminho.

    Levanta ValueError com uma frase que pode ir direto para a tela.
    """
    pais = _limpar_codigo_pais(codigo_pais)
    digitos = so_digitos(numero)

    if not digitos:
        raise ValueError("Informe o número do WhatsApp com DDD.")

    nacional = _tirar_codigo_repetido(digitos, pais)

    if pais != CODIGO_PAIS_PADRAO:
        completo = pais + nacional
        if not MINIMO_INTERNACIONAL <= len(completo) <= MAXIMO_INTERNACIONAL:
            raise ValueError(
                f"Número inválido para o país {pais}. "
                f"Use de {MINIMO_INTERNACIONAL} a {MAXIMO_INTERNACIONAL} dígitos."
            )
        return completo

    if len(nacional) - 2 not in TAMANHOS_BRASIL:
        if len(nacional) < 10:
            raise ValueError(
                "Informe o número com DDD. Exemplo: 47 99999-0000."
            )
        raise ValueError(
            "Número muito longo. Use DDD e o número, como 47 99999-0000."
        )

    ddd, resto = nacional[:2], nacional[2:]
    if ddd not in DDDS_VALIDOS:
        raise ValueError(f"DDD {ddd} não existe. Confira o número.")

    if len(resto) == 9 and not resto.startswith("9"):
        raise ValueError(
            "Celular de nove dígitos começa com 9. Confira se sobrou um dígito."
        )

    return pais + nacional


def formatar_telefone(guardado: str | None) -> str:
    """Como o número aparece na tela: "55 (47) 99999-0000".

    Enfeite, não regra. Recebe qualquer coisa e devolve algo legível, porque
    dado antigo não pode derrubar a listagem de clientes.
    """
    digitos = so_digitos(guardado)
    if not digitos:
        return guardado or ""

    if digitos.startswith(CODIGO_PAIS_PADRAO) and len(digitos) - 4 in TAMANHOS_BRASIL:
        ddd = digitos[2:4]
        resto = digitos[4:]
        meio = resto[:-4]
        fim = resto[-4:]
        return f"{CODIGO_PAIS_PADRAO} ({ddd}) {meio}-{fim}"

    if len(digitos) >= MINIMO_INTERNACIONAL:
        return f"+{digitos}"

    return guardado or ""


def _digito_verificador(base: str, peso_inicial: int) -> str:
    """Um dígito do fim do CPF, pela conta oficial da Receita."""
    soma = sum(int(d) * p for d, p in zip(base, range(peso_inicial, 1, -1)))
    resto = (soma * 10) % 11
    return "0" if resto == 10 else str(resto)


def cpf_valido(digitos: str) -> bool:
    """Os dois últimos números conferem com o resto? (RN-C02)

    É o que separa um CPF de onze algarismos quaisquer. Pega erro de digitação
    e pega o "111.111.111-11" que as pessoas usam para preencher campo chato.
    """
    if len(digitos) != DIGITOS_DO_CPF or not digitos.isdigit():
        return False
    if digitos == digitos[0] * DIGITOS_DO_CPF:
        return False

    primeiro = _digito_verificador(digitos[:9], 10)
    segundo = _digito_verificador(digitos[:10], 11)
    return digitos[9:] == primeiro + segundo


def normalizar_cpf(cpf: str | None) -> str | None:
    """Devolve os 11 dígitos do CPF, ou None quando o campo veio vazio.

    O CPF é opcional no cadastro (RF04). Não preencher não é erro; preencher
    errado é.
    """
    bruto = (cpf or "").strip()
    if not bruto:
        return None

    digitos = so_digitos(bruto)

    if len(digitos) != DIGITOS_DO_CPF:
        raise ValueError(f"O CPF tem {DIGITOS_DO_CPF} dígitos. Confira o número.")

    if not cpf_valido(digitos):
        raise ValueError("CPF inválido. Confira os números digitados.")

    return digitos


def formatar_cpf(guardado: str | None) -> str:
    """CPF na tela: "529.982.247-25". Vazio continua vazio."""
    digitos = so_digitos(guardado)
    if len(digitos) != DIGITOS_DO_CPF:
        return guardado or ""
    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
