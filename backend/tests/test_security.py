"""Testes da emissão e validação dos tokens de sessão (JWT)."""
import uuid
from datetime import timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM, criar_access_token, validar_access_token


class TestToken:
    def test_token_valido_devolve_o_vendedor(self):
        vendedor_id = uuid.uuid4()
        token = criar_access_token(vendedor_id)
        assert validar_access_token(token) == vendedor_id

    def test_token_adulterado_e_rejeitado(self):
        token = criar_access_token(uuid.uuid4())
        assert validar_access_token(token + "x") is None

    def test_token_assinado_com_outra_chave_e_rejeitado(self):
        token = jwt.encode({"sub": str(uuid.uuid4())}, "chave-errada", algorithm=ALGORITHM)
        assert validar_access_token(token) is None

    def test_token_expirado_e_rejeitado(self):
        from datetime import datetime, timezone

        expirado = jwt.encode(
            {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            settings.JWT_SECRET, algorithm=ALGORITHM,
        )
        assert validar_access_token(expirado) is None

    @pytest.mark.parametrize("texto", ["", "abc", "a.b.c", "Bearer xyz"])
    def test_textos_invalidos_nao_quebram(self, texto):
        assert validar_access_token(texto) is None

    def test_token_sem_identificacao_e_rejeitado(self):
        from datetime import datetime, timezone

        sem_sub = jwt.encode(
            {"exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            settings.JWT_SECRET, algorithm=ALGORITHM,
        )
        assert validar_access_token(sem_sub) is None

    def test_token_carrega_prazo_de_validade(self):
        token = criar_access_token(uuid.uuid4())
        dados = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        assert "exp" in dados
