"""Teste do fluxo completo do sistema, exigido no Marco M4 do RFC:

    login > cadastro de cliente > venda > cobrança automática >
    resposta do devedor > confirmação do pagamento > resumo diário

Percorre todos os módulos em conjunto, do jeito que o vendedor usaria.
"""
from datetime import date, timedelta

import pytest

from app.core.security import criar_access_token
from app.modules.agente.service import AgenteService
from app.modules.cobrancas.repository import (
    CobrancaLogRepository,
    CobrancaParcelaRepository,
    RespostaRepository,
)
from app.modules.cobrancas.service import CobrancaService
from app.modules.templates.repository import TemplateRepository
from app.modules.vendedores.models import Vendedor
from app.modules.whatsapp.client import SimuladorWhatsAppClient


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


HOJE = date.today()
NUMERO_CLIENTE = "5547999990001"
NUMERO_VENDEDOR = "5547900000000"


@pytest.fixture()
def whatsapp():
    return SimuladorWhatsAppClient()


def test_fluxo_completo_de_ponta_a_ponta(cliente_http, db, whatsapp):
    # ---------------------------------------------------------------- 1. Login
    # O vendedor entra com a conta Google; o sistema cria o perfil e emite o token.
    vendedor = Vendedor(google_email="pamela@exemplo.com", nome="Pâmela",
                        whatsapp_numero=NUMERO_VENDEDOR)
    db.add(vendedor)
    db.commit()
    db.refresh(vendedor)
    _dar_acesso(db, vendedor)
    auth = {"Authorization": f"Bearer {criar_access_token(vendedor.id)}"}

    assert cliente_http.get("/auth/me", headers=auth).json()["nome"] == "Pâmela"

    # ------------------------------------------------------ 2. Cadastro do cliente
    cliente = cliente_http.post("/clientes", headers=auth, json={
        "nome": "Rosangela Ferreira", "whatsapp_numero": NUMERO_CLIENTE,
    }).json()
    assert cliente["nome"] == "Rosangela Ferreira"

    # -------------------------------------------------------- 3. Registro da venda
    # Venda de R$ 300 em 3x, com a primeira parcela vencida há 5 dias.
    venda = cliente_http.post("/vendas", headers=auth, json={
        "cliente_id": cliente["id"], "valor_total": 300, "num_parcelas": 3,
        "data_primeira_parcela": str(HOJE - timedelta(days=5)),
    }).json()
    assert len(venda["parcelas"]) == 3
    assert venda["parcelas"][0]["status"] == "atrasada"

    perfil = cliente_http.get(f"/clientes/{cliente['id']}/perfil", headers=auth).json()
    assert perfil["saldo_devedor"] == 300.0

    # ------------------------------------------------- 4. Cobrança automática
    cobranca = CobrancaService(
        CobrancaLogRepository(db), CobrancaParcelaRepository(db),
        TemplateRepository(db), whatsapp,
    )
    enviados = cobranca.varrer_e_cobrar(vendedor.id, dias_antecedencia=3, ignorar_horario=True)
    assert len(enviados) >= 1
    assert enviados[0].status == "enviado"

    numero, texto = whatsapp.enviadas[0]
    assert numero == NUMERO_CLIENTE
    assert "Rosangela Ferreira" in texto
    assert "R$ 100,00" in texto
    assert "1 - Já paguei" in texto
    assert "{" not in texto  # nenhuma variável ficou por substituir

    # O envio aparece no histórico de cobranças.
    log = cliente_http.get("/cobrancas", headers=auth).json()
    assert len(log) >= 1
    assert log[0]["cliente_nome"] == "Rosangela Ferreira"

    # ------------------------------------------------- 5. Resposta do devedor
    resposta = cliente_http.post("/whatsapp/webhook",
                                 json={"numero": NUMERO_CLIENTE, "texto": "1"}).json()
    assert resposta["processada"] is True
    assert resposta["opcao"] == "1_ja_paguei"

    # A parcela fica aguardando conferência — o pagamento NÃO foi dado como certo.
    perfil = cliente_http.get(f"/clientes/{cliente['id']}/perfil", headers=auth).json()
    parcela = perfil["vendas"][0]["parcelas"][0]
    assert parcela["status"] == "aguardando_confirmacao"
    assert perfil["saldo_devedor"] == 300.0  # saldo intacto

    # ------------------------------------------- 6. Confirmação pelo vendedor
    assert cliente_http.post(f"/parcelas/{parcela['id']}/pagar",
                             headers=auth).status_code == 200

    perfil = cliente_http.get(f"/clientes/{cliente['id']}/perfil", headers=auth).json()
    assert perfil["vendas"][0]["parcelas"][0]["status"] == "paga"
    assert perfil["saldo_devedor"] == 200.0

    # O painel reflete o pagamento.
    painel = cliente_http.get("/relatorios/dashboard", headers=auth).json()
    assert painel["total_a_receber"] == 200.0
    assert painel["recebido_no_mes"] == 100.0

    # --------------------------------------------------- 7. Resumo diário
    agente = AgenteService(
        CobrancaParcelaRepository(db), RespostaRepository(db),
        CobrancaLogRepository(db), whatsapp,
    )
    resumo = agente.enviar_resumo(vendedor.id, vendedor.whatsapp_numero, HOJE)
    assert resumo is not None
    assert resumo.tipo == "resumo"

    destinatario, corpo = whatsapp.enviadas[-1]
    assert destinatario == NUMERO_VENDEDOR
    assert "Cobranças enviadas" in corpo
    assert "Pagamentos confirmados: 1" in corpo
    assert "R$ 100,00" in corpo
    assert "Já paguei: 1" in corpo

    # ------------------------------------------------------ 8. Relatório em PDF
    pdf = cliente_http.get("/relatorios/pdf", headers=auth)
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")


def test_isolamento_entre_contas_no_fluxo(cliente_http, db):
    """M4: dois vendedores distintos nunca enxergam os dados um do outro."""
    a = Vendedor(google_email="a@exemplo.com", nome="Vendedora A")
    b = Vendedor(google_email="b@exemplo.com", nome="Vendedora B")
    db.add_all([a, b])
    db.commit()
    db.refresh(a)
    db.refresh(b)
    _dar_acesso(db, a, b)
    auth_a = {"Authorization": f"Bearer {criar_access_token(a.id)}"}
    auth_b = {"Authorization": f"Bearer {criar_access_token(b.id)}"}

    cliente_a = cliente_http.post("/clientes", headers=auth_a, json={
        "nome": "Cliente da A", "whatsapp_numero": "5547911111111"}).json()
    cliente_http.post("/vendas", headers=auth_a, json={
        "cliente_id": cliente_a["id"], "valor_total": 500, "num_parcelas": 2,
        "data_primeira_parcela": str(HOJE)})

    # A vendedora B não vê nada: nem clientes, nem valores, nem o perfil.
    assert cliente_http.get("/clientes", headers=auth_b).json() == []
    assert cliente_http.get("/relatorios/dashboard", headers=auth_b).json()["total_a_receber"] == 0
    assert cliente_http.get(f"/clientes/{cliente_a['id']}/perfil",
                            headers=auth_b).status_code == 404
    assert cliente_http.get("/cobrancas", headers=auth_b).json() == []

    # E a vendedora A continua vendo os próprios dados.
    assert cliente_http.get("/relatorios/dashboard", headers=auth_a).json()["total_a_receber"] == 500.0
