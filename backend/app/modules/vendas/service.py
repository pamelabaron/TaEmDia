"""Regras de negócio de vendas e parcelas."""
import calendar
import uuid
from datetime import date
from decimal import Decimal

from app.modules.clientes.repository import ClienteRepository
from app.modules.vendas.models import Parcela, Venda
from app.modules.vendas.repository import ParcelaRepository, VendaRepository


class ClienteInexistenteError(Exception):
    pass


class VendaNaoEncontradaError(Exception):
    pass


class ParcelaNaoEncontradaError(Exception):
    pass


class OperacaoInvalidaError(Exception):
    def __init__(self, mensagem: str):
        self.mensagem = mensagem


def _somar_meses(d: date, meses: int) -> date:
    """Soma meses a uma data, ajustando o dia ao último dia do mês quando necessário
    (ex.: 31/01 + 1 mês => 28/02)."""
    total = d.month - 1 + meses
    ano = d.year + total // 12
    mes = total % 12 + 1
    dia = min(d.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def _dividir_valor(valor_total: float, num_parcelas: int) -> list[Decimal]:
    """Divide o valor em parcelas de 2 casas, jogando os centavos restantes nas
    últimas parcelas para que a soma feche exatamente com o total."""
    total_centavos = int(round(valor_total * 100))
    base = total_centavos // num_parcelas
    resto = total_centavos - base * num_parcelas
    valores = []
    for i in range(num_parcelas):
        centavos = base + (1 if i >= num_parcelas - resto else 0)
        valores.append(Decimal(centavos) / 100)
    return valores


def calcular_status(parcela: Parcela, hoje: date | None = None) -> str:
    """Deriva o status da parcela conforme o ciclo de vida do RFC (RN09)."""
    hoje = hoje or date.today()
    if parcela.data_pagamento is not None:
        return "paga"
    if parcela.aguardando_confirmacao:
        return "aguardando_confirmacao"
    if parcela.data_vencimento < hoje:
        return "atrasada"
    return "pendente"


def _parcela_para_dict(parcela: Parcela) -> dict:
    return {
        "id": parcela.id,
        "numero_parcela": parcela.numero_parcela,
        "valor": float(parcela.valor),
        "data_vencimento": parcela.data_vencimento,
        "data_pagamento": parcela.data_pagamento,
        "status": calcular_status(parcela),
    }


def venda_para_dict(venda: Venda) -> dict:
    return {
        "id": venda.id,
        "cliente_id": venda.cliente_id,
        "valor_total": float(venda.valor_total),
        "num_parcelas": venda.num_parcelas,
        "data_primeira_parcela": venda.data_primeira_parcela,
        "status": venda.status,
        "criado_em": venda.criado_em,
        "parcelas": [_parcela_para_dict(p) for p in venda.parcelas],
    }


class VendasService:
    def __init__(self, vendas: VendaRepository, parcelas: ParcelaRepository, clientes: ClienteRepository):
        self.vendas = vendas
        self.parcelas = parcelas
        self.clientes = clientes

    def registrar_venda(
        self, vendedor_id: uuid.UUID, cliente_id: uuid.UUID,
        valor_total: float, num_parcelas: int, data_primeira: date,
    ) -> Venda:
        # Garante que o cliente é do próprio vendedor (isolamento).
        cliente = self.clientes.buscar_por_id(vendedor_id, cliente_id)
        if not cliente or not cliente.ativo:
            raise ClienteInexistenteError()

        venda = Venda(
            vendedor_id=vendedor_id,
            cliente_id=cliente_id,
            valor_total=Decimal(str(round(valor_total, 2))),
            num_parcelas=num_parcelas,
            data_primeira_parcela=data_primeira,
        )
        valores = _dividir_valor(valor_total, num_parcelas)
        for i in range(num_parcelas):
            venda.parcelas.append(Parcela(
                numero_parcela=i + 1,
                valor=valores[i],
                data_vencimento=_somar_meses(data_primeira, i),
            ))
        return self.vendas.criar(venda)

    def obter_venda(self, vendedor_id: uuid.UUID, venda_id: uuid.UUID) -> Venda:
        venda = self.vendas.buscar_por_id(vendedor_id, venda_id)
        if not venda:
            raise VendaNaoEncontradaError()
        return venda

    def confirmar_pagamento(self, vendedor_id: uuid.UUID, parcela_id: uuid.UUID) -> Parcela:
        """Marca a parcela como paga (RF12). Só o vendedor confirma (RN12)."""
        parcela = self.parcelas.buscar_por_id(vendedor_id, parcela_id)
        if not parcela:
            raise ParcelaNaoEncontradaError()
        if parcela.data_pagamento is not None:
            raise OperacaoInvalidaError("Esta parcela já está paga.")
        parcela.data_pagamento = date.today()
        parcela.aguardando_confirmacao = False
        self.parcelas.salvar()
        # (Sprint 3+) aqui dispararemos o recálculo do ranking do cliente.
        return parcela

    def cancelar_venda(self, vendedor_id: uuid.UUID, venda_id: uuid.UUID) -> Venda:
        """Cancela uma venda (RF16)."""
        venda = self.vendas.buscar_por_id(vendedor_id, venda_id)
        if not venda:
            raise VendaNaoEncontradaError()
        if venda.status == "cancelada":
            raise OperacaoInvalidaError("Esta venda já está cancelada.")
        venda.status = "cancelada"
        self.vendas.salvar()
        return venda

    def calcular_saldo_devedor(self, venda: Venda) -> Decimal:
        """Soma das parcelas ainda não pagas de uma venda ativa."""
        if venda.status == "cancelada":
            return Decimal("0.00")
        return sum((p.valor for p in venda.parcelas if p.data_pagamento is None), Decimal("0.00"))

    def obter_perfil(self, vendedor_id: uuid.UUID, cliente_id: uuid.UUID) -> dict:
        """Monta o perfil do cliente com vendas, parcelas e saldo devedor (RF07/RF08)."""
        cliente = self.clientes.buscar_por_id(vendedor_id, cliente_id)
        if not cliente:
            raise ClienteInexistenteError()
        vendas = self.vendas.listar_por_cliente(vendedor_id, cliente_id)
        saldo = sum((self.calcular_saldo_devedor(v) for v in vendas), Decimal("0.00"))
        return {
            "id": cliente.id,
            "nome": cliente.nome,
            "whatsapp_numero": cliente.whatsapp_numero,
            "cpf": cliente.cpf,
            "endereco": cliente.endereco,
            "saldo_devedor": float(saldo),
            "vendas": [venda_para_dict(v) for v in vendas],
        }
