"""assinatura de cortesia para contas existentes

Quem já usava o sistema antes da assinatura existir não pode ser bloqueado sem
aviso: do ponto de vista dessas pessoas, nada mudou na véspera. Esta migration
dá a elas os mesmos 7 dias de teste que uma conta nova recebe (RN-A01),
contados da data em que a migration roda.

Só alcança vendedores que ainda não têm linha em `assinatura`, então rodar de
novo não estende o prazo de ninguém.

Revision ID: 612e2956d2f8
Revises: 35a80494d517
Create Date: 2026-09-13 20:21:46.848447
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# identificadores da revisão, usados pelo Alembic.
revision: str = '612e2956d2f8'
down_revision: Union[str, None] = '35a80494d517'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DIAS_DE_TESTE = 7


def upgrade() -> None:
    op.execute(
        sa.text(
            f"""
            INSERT INTO assinatura (id, vendedor_id, valido_ate, origem,
                                    criado_em, atualizado_em)
            SELECT gen_random_uuid(),
                   v.id,
                   CURRENT_DATE + INTERVAL '{DIAS_DE_TESTE} days',
                   'teste',
                   NOW(),
                   NOW()
              FROM vendedor v
             WHERE NOT EXISTS (
                   SELECT 1 FROM assinatura a WHERE a.vendedor_id = v.id
             )
            """
        )
    )


def downgrade() -> None:
    # Remove apenas as cortesias que esta migration criou: as que ainda estão
    # em "teste" e nunca foram renovadas. Assinaturas pagas ficam intactas.
    op.execute(sa.text("DELETE FROM assinatura WHERE origem = 'teste'"))
