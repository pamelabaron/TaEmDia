"""Classificação de clientes por comportamento de pagamento (RN15/RN16).

Categorias:
  - bom          : >= 90% das parcelas pagas em dia E média de atraso < 3 dias
  - inadimplente : > 30% das parcelas em atraso, OU parcela em aberto há > 60 dias
  - regular      : os demais (atrasos ocasionais)
  - sem_historico: sem parcelas com comportamento avaliável no período
"""
import uuid
from dataclasses import dataclass
from datetime import date


@dataclass
class ParcelaRanking:
    data_vencimento: date
    data_pagamento: date | None


@dataclass
class Classificacao:
    categoria: str
    percentual_em_dia: float
    media_dias_atraso: float
    total_avaliadas: int


def classificar(parcelas: list[ParcelaRanking], hoje: date) -> Classificacao:
    """Avalia apenas parcelas com comportamento definido: já pagas, ou vencidas e
    ainda em aberto. Parcelas futuras (ainda não vencidas) são neutras e ignoradas."""
    avaliadas = 0
    em_dia = 0
    atrasadas = 0
    soma_atraso = 0
    max_dias_aberto = 0

    for p in parcelas:
        if p.data_pagamento is not None:
            atraso = (p.data_pagamento - p.data_vencimento).days
            avaliadas += 1
            if atraso <= 0:
                em_dia += 1
            else:
                atrasadas += 1
                soma_atraso += atraso
        else:
            dias = (hoje - p.data_vencimento).days
            if dias > 0:  # vencida e em aberto
                avaliadas += 1
                atrasadas += 1
                soma_atraso += dias
                max_dias_aberto = max(max_dias_aberto, dias)
            # futura em aberto: neutra, ignorada

    if avaliadas == 0:
        return Classificacao("sem_historico", 0.0, 0.0, 0)

    perc_em_dia = em_dia / avaliadas * 100
    media_atraso = soma_atraso / avaliadas
    frac_atraso = atrasadas / avaliadas

    if frac_atraso > 0.30 or max_dias_aberto > 60:
        categoria = "inadimplente"
    elif perc_em_dia >= 90 and media_atraso < 3:
        categoria = "bom"
    else:
        categoria = "regular"

    return Classificacao(categoria, round(perc_em_dia, 1), round(media_atraso, 1), avaliadas)
