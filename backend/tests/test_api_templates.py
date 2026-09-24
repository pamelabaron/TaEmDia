"""Testes da API de templates de mensagem."""
import uuid


def _dar_acesso(db, *vendedores):
    """Vigência de teste para vendedores criados direto no banco.

    O login real cria esses 7 dias sozinho (RN-A01); testes que inserem o
    vendedor na mão precisam fazer o mesmo, senão a escrita responde 402.
    """
    from datetime import date, timedelta

    from app.modules.assinatura.models import Assinatura

    for v in vendedores:
        db.add(Assinatura(vendedor_id=v.id,
                          valido_ate=date.today() + timedelta(days=7),
                          origem="teste"))
    db.commit()



class TestTemplates:
    def test_exige_autenticacao(self, cliente_http):
        assert cliente_http.get("/templates").status_code == 401

    def test_primeira_consulta_cria_os_tres_padroes(self, cliente_http, cabecalho_auth):
        lista = cliente_http.get("/templates", headers=cabecalho_auth).json()
        assert len(lista) == 3
        assert {t["tipo"] for t in lista} == {"lembrete", "vencimento", "atraso"}
        assert all(t["is_padrao"] for t in lista)

    def test_nao_duplica_os_padroes(self, cliente_http, cabecalho_auth):
        cliente_http.get("/templates", headers=cabecalho_auth)
        segunda = cliente_http.get("/templates", headers=cabecalho_auth).json()
        assert len(segunda) == 3

    def test_lista_de_variaveis(self, cliente_http, cabecalho_auth):
        resp = cliente_http.get("/templates/variaveis", headers=cabecalho_auth)
        assert resp.status_code == 200
        assert "nome_cliente" in resp.json()

    def test_previa_substitui_as_variaveis(self, cliente_http, cabecalho_auth):
        resp = cliente_http.post("/templates/preview", headers=cabecalho_auth,
                                 json={"corpo": "Ola {nome_cliente}, deve {valor_parcela}"})
        resultado = resp.json()["resultado"]
        assert "{" not in resultado
        assert "Maria Silva" in resultado

    def _primeiro_id(self, cliente_http, cabecalho_auth):
        return cliente_http.get("/templates", headers=cabecalho_auth).json()[0]["id"]

    def test_edita_o_corpo(self, cliente_http, cabecalho_auth):
        tid = self._primeiro_id(cliente_http, cabecalho_auth)
        resp = cliente_http.patch("/templates/" + tid, headers=cabecalho_auth,
                                  json={"corpo": "Oi {nome_cliente}!"})
        assert resp.status_code == 200
        assert resp.json()["corpo"] == "Oi {nome_cliente}!"

    def test_edita_o_titulo(self, cliente_http, cabecalho_auth):
        tid = self._primeiro_id(cliente_http, cabecalho_auth)
        resp = cliente_http.patch("/templates/" + tid, headers=cabecalho_auth,
                                  json={"titulo": "Cobranca amigavel"})
        assert resp.json()["titulo"] == "Cobranca amigavel"

    def test_desativa_um_template(self, cliente_http, cabecalho_auth):
        tid = self._primeiro_id(cliente_http, cabecalho_auth)
        resp = cliente_http.patch("/templates/" + tid, headers=cabecalho_auth,
                                  json={"ativo": False})
        assert resp.json()["ativo"] is False

    def test_template_inexistente(self, cliente_http, cabecalho_auth):
        resp = cliente_http.patch("/templates/" + str(uuid.uuid4()), headers=cabecalho_auth,
                                  json={"titulo": "X"})
        assert resp.status_code == 404

    def test_nao_edita_template_de_outra_conta(self, cliente_http, cabecalho_auth, db):
        from app.core.security import criar_access_token
        from app.modules.vendedores.models import Vendedor

        tid = self._primeiro_id(cliente_http, cabecalho_auth)
        outro = Vendedor(google_email="outro@tpl.com", nome="Outro")
        db.add(outro)
        db.commit()
        db.refresh(outro)
        _dar_acesso(db, outro)
        resp = cliente_http.patch(
            "/templates/" + tid,
            headers={"Authorization": "Bearer " + criar_access_token(outro.id)},
            json={"titulo": "Invadido"},
        )
        assert resp.status_code == 404
