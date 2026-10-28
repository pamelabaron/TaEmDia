"""Todo campo que a pessoa digita precisa ter limite (RN-L01).

Campo sem teto aceita texto de qualquer tamanho e número de qualquer grandeza.
O estrago não é teórico:

- nome de cliente sem limite enche a listagem e quebra o layout de todas as
  telas que o mostram;
- valor de venda sem teto transforma um erro de digitação (50000 em vez de
  500,00) numa dívida de cinquenta mil reais, cobrada de verdade pelo agente;
- corpo de mensagem sem limite estoura o tamanho que o WhatsApp aceita, e a
  cobrança falha no envio, calada;
- texto imenso em qualquer campo é a forma mais barata de derrubar um servidor.

Este arquivo não testa um campo de cada vez: ele **varre** todos os formatos de
entrada da API e reprova o que não tiver limite. Assim, campo novo criado daqui
a seis meses também precisa declarar o seu, em vez de passar despercebido.

A varredura lê o contrato que o próprio Pydantic publica (o mesmo que aparece
na documentação em /docs), e não as anotações do código. A primeira tentativa
olhava os tipos do Python e tinha um ponto cego: o `EmailStr` não herda de
texto, então um e-mail sem tamanho máximo passava limpo pela conferência.
"""
import importlib
import io
import pkgutil

import pytest
from pydantic import BaseModel

import app.modules

#: Formatos que a API recebe de fora. Os de saída (Out) não entram: o limite
#: protege de quem escreve, não de quem lê.
SUFIXOS_DE_ENTRADA = ("Create", "Update", "In")

#: Campos que não levam limite, com o motivo.
DISPENSADOS = {
    # Identificadores gerados pelo sistema, nunca digitados por ninguém.
    "id", "cliente_id", "parcela_id", "vendedor_id", "venda_id",
}

#: Formatos que já têm tamanho fixo pela própria definição.
FORMATOS_LIMITADOS = {"uuid", "uuid4", "date", "time", "date-time", "binary"}


def _modelos_de_entrada() -> list[tuple[str, type[BaseModel]]]:
    """Todos os schemas de entrada declarados nos módulos da aplicação."""
    encontrados: dict[str, type[BaseModel]] = {}

    for info in pkgutil.walk_packages(app.modules.__path__, "app.modules."):
        if not info.name.endswith(".schemas"):
            continue
        modulo = importlib.import_module(info.name)
        for nome in dir(modulo):
            obj = getattr(modulo, nome)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseModel)
                and obj is not BaseModel
                and nome.endswith(SUFIXOS_DE_ENTRADA)
            ):
                encontrados[f"{info.name}.{nome}"] = obj

    return sorted(encontrados.items())


def _ramos(definicao: dict) -> list[dict]:
    """As formas que o campo aceita.

    Um campo opcional vira "anyOf": o texto de um lado, o nulo do outro. O
    limite precisa estar no ramo do texto, não no campo inteiro.
    """
    if "anyOf" in definicao:
        return definicao["anyOf"]
    return [definicao]


def _campos(modelo: type[BaseModel]):
    """Percorre os campos do contrato publicado, já desembrulhados."""
    esquema = modelo.model_json_schema()
    for nome, definicao in esquema.get("properties", {}).items():
        if nome in DISPENSADOS:
            continue
        for ramo in _ramos(definicao):
            yield nome, ramo


MODELOS = _modelos_de_entrada()


def test_a_varredura_enxerga_os_schemas_da_aplicacao():
    """Se a varredura vier vazia, os outros testes passam sem testar nada."""
    nomes = [nome for nome, _ in MODELOS]
    assert len(nomes) >= 5, f"A varredura achou poucos schemas: {nomes}"
    assert any("ClienteCreate" in nome for nome in nomes)
    assert any("VendaCreate" in nome for nome in nomes)
    assert any("ConfiguracaoUpdate" in nome for nome in nomes)


def test_a_varredura_enxerga_campo_de_email():
    """Protege o próprio teste: o e-mail já escapou uma vez por ser tipo especial."""
    achou = any(
        nome_do_campo == "email_resumo" and ramo.get("type") == "string"
        for _, modelo in MODELOS
        for nome_do_campo, ramo in _campos(modelo)
    )
    assert achou, "A varredura deixou de enxergar o campo de e-mail do resumo"


def test_todo_campo_de_texto_tem_tamanho_maximo():
    sem_limite = []

    for nome_do_modelo, modelo in MODELOS:
        for nome_do_campo, ramo in _campos(modelo):
            if ramo.get("type") != "string" or "enum" in ramo:
                continue
            if ramo.get("format") in FORMATOS_LIMITADOS:
                continue
            if "maxLength" not in ramo:
                sem_limite.append(f"{nome_do_modelo}.{nome_do_campo}")

    assert not sem_limite, (
        "Campos de texto sem tamanho máximo: "
        + ", ".join(sorted(set(sem_limite)))
        + ". Use Field(max_length=...) em cada um."
    )


def test_todo_campo_de_numero_tem_teto():
    """Mínimo sozinho não basta: "maior que zero" aceita um bilhão."""
    sem_teto = []

    for nome_do_modelo, modelo in MODELOS:
        for nome_do_campo, ramo in _campos(modelo):
            if ramo.get("type") not in ("integer", "number"):
                continue
            if not ({"maximum", "exclusiveMaximum"} & set(ramo)):
                sem_teto.append(f"{nome_do_modelo}.{nome_do_campo}")

    assert not sem_teto, (
        "Campos numéricos sem valor máximo: "
        + ", ".join(sorted(set(sem_teto)))
        + ". Use Field(le=...) em cada um."
    )


def test_todo_campo_de_numero_tem_piso():
    """Valor negativo em dinheiro ou em quantidade nunca faz sentido aqui."""
    sem_piso = []

    for nome_do_modelo, modelo in MODELOS:
        for nome_do_campo, ramo in _campos(modelo):
            if ramo.get("type") not in ("integer", "number"):
                continue
            if not ({"minimum", "exclusiveMinimum"} & set(ramo)):
                sem_piso.append(f"{nome_do_modelo}.{nome_do_campo}")

    assert not sem_piso, (
        "Campos numéricos sem valor mínimo: "
        + ", ".join(sorted(set(sem_piso)))
        + ". Use Field(ge=...) ou Field(gt=...) em cada um."
    )


#: A assinatura de um PNG de verdade, seguida de enchimento. Bytes quaisquer
#: sao recusados pela checagem de conteudo, e ai o teste passaria pelo motivo
#: errado: o 422 viria do arquivo invalido, nao do valor fora da faixa.
#:
#: Montada por numero, e nao por escapes, de proposito: escrita como texto
#: com barras invertidas, esta constante ja entrou no arquivo com bytes nulos
#: de verdade, e o Python recusou o arquivo inteiro.
PNG = bytes([0x89]) + b"PNG" + bytes([0x0D, 0x0A, 0x1A, 0x0A]) + b"0" * 64


def _comprovante():
    return {"arquivo": ("comprovante.png", io.BytesIO(PNG), "image/png")}


@pytest.fixture
def cliente_criado(cliente_http, cabecalho_auth) -> str:
    """Um cliente de verdade, para as vendas dos testes terem a quem pertencer."""
    resp = cliente_http.post("/clientes", headers=cabecalho_auth, json={
        "nome": "Rosangela Ferreira",
        "whatsapp_numero": "5547999990123",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestLimitesQueAVarreduraNaoAlcanca:
    """Data e valor em formulário não aparecem como texto nem como número puro.

    A varredura acima lê o contrato publicado e, para esses dois, ele não diz
    nada: data é "format: date" (sem faixa) e o valor do comprovante chega por
    formulário de envio de arquivo, fora de qualquer schema. Ficam aqui, um a um.
    """

    def test_data_da_primeira_parcela_nao_aceita_ano_distante(self, cliente_http, cabecalho_auth, cliente_criado):
        """Ano 9999 é sempre engano de digitação, nunca um carnê de verdade."""
        resp = cliente_http.post("/vendas", headers=cabecalho_auth, json={
            "cliente_id": cliente_criado,
            "valor_total": 300.0,
            "num_parcelas": 3,
            "data_primeira_parcela": "9999-01-01",
        })
        assert resp.status_code == 422

    def test_data_da_primeira_parcela_nao_aceita_passado_distante(self, cliente_http, cabecalho_auth, cliente_criado):
        resp = cliente_http.post("/vendas", headers=cabecalho_auth, json={
            "cliente_id": cliente_criado,
            "valor_total": 300.0,
            "num_parcelas": 3,
            "data_primeira_parcela": "1990-01-01",
        })
        assert resp.status_code == 422

    def test_venda_retroativa_recente_continua_valendo(self, cliente_http, cabecalho_auth, cliente_criado):
        """Vendedor que lança hoje a venda do mês passado é caso comum."""
        from datetime import date, timedelta

        resp = cliente_http.post("/vendas", headers=cabecalho_auth, json={
            "cliente_id": cliente_criado,
            "valor_total": 300.0,
            "num_parcelas": 3,
            "data_primeira_parcela": str(date.today() - timedelta(days=30)),
        })
        assert resp.status_code == 201

    def test_valor_da_venda_tem_teto(self, cliente_http, cabecalho_auth, cliente_criado):
        """Quem digita 50000 querendo 500,00 seria cobrado de verdade."""
        resp = cliente_http.post("/vendas", headers=cabecalho_auth, json={
            "cliente_id": cliente_criado,
            "valor_total": 9_999_999.0,
            "num_parcelas": 3,
            "data_primeira_parcela": "2026-11-05",
        })
        assert resp.status_code == 422

    def test_comprovante_de_valor_absurdo_e_recusado(self, cliente_http, cabecalho_auth):
        resp = cliente_http.post(
            "/assinatura/comprovante",
            headers=cabecalho_auth,
            data={"valor": "999999"},
            files=_comprovante(),
        )
        assert resp.status_code == 422

    def test_comprovante_de_valor_normal_passa(self, cliente_http, cabecalho_auth):
        resp = cliente_http.post(
            "/assinatura/comprovante",
            headers=cabecalho_auth,
            data={"valor": "49.90"},
            files=_comprovante(),
        )
        assert resp.status_code in (200, 201)
