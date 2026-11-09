"""Regras de negócio da biblioteca, sem dependência de banco ou HTTP."""

from datetime import date

PRAZO_EMPRESTIMO_DIAS = 14
MULTA_POR_DIA = 2.0
LIMITE_EMPRESTIMOS_ATIVOS = 3


def calcular_multa(data_prevista: date, data_devolucao: date) -> float:
    dias_de_atraso = (data_devolucao - data_prevista).days
    if dias_de_atraso <= 0:
        return 0.0
    return dias_de_atraso * MULTA_POR_DIA
