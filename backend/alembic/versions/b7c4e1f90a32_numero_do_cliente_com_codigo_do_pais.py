"""numero do cliente com codigo do pais

Acerta os números já cadastrados antes da RN-C01.

Antes desta regra nada conferia o telefone, e números foram salvos sem o 55.
O WhatsApp exige o código do país: uma cobrança enviada para "4799..." não
chega a ninguém, e nenhum erro aparece no caminho. A falha só apareceria pela
boca do vendedor, meses depois, como "o cliente disse que nunca recebeu".

O CPF também passa por aqui, só para tirar ponto e traço de quem foi cadastrado
com pontuação. CPF que não passa na conta dos dígitos verificadores é deixado
como está: apagar dado de cliente por conta de uma regra nova seria pior que o
dado torto. Ele será corrigido na próxima edição do cadastro, quando a API
recusar o valor inválido.

Revision ID: b7c4e1f90a32
Revises: ff6aa3d8bde9
Create Date: 2026-09-26
"""
import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# identificadores da revisão, usados pelo Alembic.
revision: str = 'b7c4e1f90a32'
down_revision: Union[str, None] = 'ff6aa3d8bde9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CODIGO_BRASIL = "55"


def _so_digitos(texto: str | None) -> str:
    return re.sub(r"\D", "", texto or "")


def _com_codigo_do_pais(guardado: str | None) -> str | None:
    """Acrescenta o 55 quando o número está sem ele.

    Só mexe no que tem cara de número brasileiro sem código do país: 10 ou 11
    dígitos. Qualquer outro tamanho fica intocado, porque pode ser número de
    fora, que já tem o código certo.
    """
    digitos = _so_digitos(guardado)
    if len(digitos) in (10, 11):
        return CODIGO_BRASIL + digitos
    return None


def upgrade() -> None:
    conexao = op.get_bind()

    linhas = conexao.execute(
        sa.text("SELECT id, vendedor_id, whatsapp_numero, cpf FROM cliente")
    ).fetchall()

    novos_numeros: dict[str, str] = {}
    for linha in linhas:
        corrigido = _com_codigo_do_pais(linha.whatsapp_numero)
        if corrigido and corrigido != linha.whatsapp_numero:
            novos_numeros[str(linha.id)] = corrigido

    # O banco não deixa dois clientes do mesmo vendedor com o mesmo número.
    # Se o mesmo telefone estiver salvo em dois formatos, acertar os dois
    # criaria o conflito. Melhor parar e avisar do que perder um cadastro.
    ja_ocupados = {
        (str(linha.vendedor_id), linha.whatsapp_numero)
        for linha in linhas
        if str(linha.id) not in novos_numeros
    }
    vistos = set()
    for linha in linhas:
        novo = novos_numeros.get(str(linha.id))
        if novo is None:
            continue
        chave = (str(linha.vendedor_id), novo)
        if chave in ja_ocupados or chave in vistos:
            raise RuntimeError(
                f"O cliente {linha.id} ficaria com o número {novo}, que já "
                "existe nessa carteira. Junte os dois cadastros na mão antes "
                "de rodar esta migração."
            )
        vistos.add(chave)

    for id_cliente, numero in novos_numeros.items():
        conexao.execute(
            sa.text("UPDATE cliente SET whatsapp_numero = :n WHERE id = :i"),
            {"n": numero, "i": id_cliente},
        )

    for linha in linhas:
        if not linha.cpf:
            continue
        limpo = _so_digitos(linha.cpf)
        if limpo and limpo != linha.cpf:
            conexao.execute(
                sa.text("UPDATE cliente SET cpf = :c WHERE id = :i"),
                {"c": limpo, "i": str(linha.id)},
            )


def downgrade() -> None:
    """Tira o 55 dos números brasileiros, voltando ao formato antigo."""
    conexao = op.get_bind()

    linhas = conexao.execute(
        sa.text("SELECT id, whatsapp_numero FROM cliente")
    ).fetchall()

    for linha in linhas:
        digitos = _so_digitos(linha.whatsapp_numero)
        if digitos.startswith(CODIGO_BRASIL) and len(digitos) in (12, 13):
            conexao.execute(
                sa.text("UPDATE cliente SET whatsapp_numero = :n WHERE id = :i"),
                {"n": digitos[2:], "i": str(linha.id)},
            )
