"""Varredura: todo endpoint de escrita exige assinatura válida.

Este é o teste que sustenta a decisão de aplicar a trava por dependência em vez
de middleware. Se alguém criar um endpoint de escrita amanhã e esquecer de
protegê-lo, a suíte quebra aqui — não em produção.

Ver docs/superpowers/specs/2026-09-13-assinatura-design.md, seção 2.
"""
from fastapi.routing import APIRoute

from app.main import app
from app.modules.assinatura.deps import exigir_assinatura_ativa

METODOS_DE_ESCRITA = {"POST", "PUT", "PATCH", "DELETE"}

#: Endpoints de escrita deliberadamente abertos, com o motivo de cada um.
#: Mexer nesta lista é uma decisão de segurança — não a use para calar o teste.
EXCECOES = {
    ("/whatsapp/webhook", "POST"): "é a resposta do devedor, não do assinante",
    ("/templates/preview", "POST"): "só monta o texto, não grava",
    ("/assinatura/comprovante", "POST"): "é como a pessoa volta a ter acesso",
    # A conferência é da administradora e roda atrás de exigir_admin. Pedir
    # assinatura aqui seria circular: quem libera assinaturas ficaria preso
    # pela própria trava que administra.
    ("/admin/comprovantes/{pagamento_id}/aprovar", "POST"): "protegido por exigir_admin",
    ("/admin/comprovantes/{pagamento_id}/recusar", "POST"): "protegido por exigir_admin",
}

#: Exceções que precisam estar protegidas por outra dependência, e qual.
PROTEGIDAS_POR_ADMIN = {
    ("/admin/comprovantes/{pagamento_id}/aprovar", "POST"),
    ("/admin/comprovantes/{pagamento_id}/recusar", "POST"),
}


def _rotas_de_escrita() -> list[tuple[str, str, APIRoute]]:
    """Todas as rotas registradas que gravam algo."""
    achadas = []
    for rota in app.routes:
        if not isinstance(rota, APIRoute):
            continue
        for metodo in rota.methods or set():
            if metodo in METODOS_DE_ESCRITA:
                achadas.append((rota.path, metodo, rota))
    return achadas


def _tem_trava(rota: APIRoute) -> bool:
    """A dependência da assinatura aparece em algum ponto da rota?"""
    return any(
        d.call is exigir_assinatura_ativa for d in rota.dependant.dependencies
    ) or any(
        getattr(d, "dependency", None) is exigir_assinatura_ativa
        for d in (rota.dependencies or [])
    )


def test_existe_rota_de_escrita_para_varrer():
    """Guarda contra o teste passar por não ter encontrado nada."""
    assert len(_rotas_de_escrita()) >= 10


def test_toda_rota_de_escrita_exige_assinatura():
    desprotegidas = [
        f"{metodo} {caminho}"
        for caminho, metodo, rota in _rotas_de_escrita()
        if (caminho, metodo) not in EXCECOES and not _tem_trava(rota)
    ]
    assert not desprotegidas, (
        "Endpoint de escrita sem trava de assinatura: "
        + ", ".join(sorted(desprotegidas))
        + ". Aplique exigir_assinatura_ativa ou registre em EXCECOES com o motivo."
    )


def test_excecoes_ainda_existem():
    """Se um endpoint da lista de exceções sumiu ou mudou de caminho, a lista
    ficou mentindo — e uma exceção esquecida é uma porta aberta."""
    registradas = {(caminho, metodo) for caminho, metodo, _ in _rotas_de_escrita()}
    fantasmas = [f"{m} {c}" for (c, m) in EXCECOES if (c, m) not in registradas]
    assert not fantasmas, (
        "Exceção listada que não corresponde a nenhuma rota: " + ", ".join(sorted(fantasmas))
    )


def test_excecoes_de_admin_estao_protegidas_por_admin():
    """Uma exceção da trava de assinatura não pode ser um endpoint aberto:
    as da administração precisam exigir admin."""
    from app.modules.assinatura.deps import exigir_admin

    desprotegidas = []
    for caminho, metodo, rota in _rotas_de_escrita():
        if (caminho, metodo) not in PROTEGIDAS_POR_ADMIN:
            continue
        tem = any(d.call is exigir_admin for d in rota.dependant.dependencies)
        if not tem:
            desprotegidas.append(f"{metodo} {caminho}")
    assert not desprotegidas, (
        "Endpoint listado como \"protegido por admin\" sem exigir_admin: "
        + ", ".join(sorted(desprotegidas))
    )
