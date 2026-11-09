"""Operações com regra de negócio, usadas tanto pela API quanto pelas páginas.

Não sabem nada de HTTP: sinalizam problemas com exceções próprias, e quem
chama decide se vira 404/409 (API) ou uma mensagem na tela (páginas).
"""

import sqlite3
from datetime import date, timedelta

from app import repositorio
from app.datas import hoje
from app.regras import LIMITE_EMPRESTIMOS_ATIVOS, PRAZO_EMPRESTIMO_DIAS, calcular_multa


class NaoEncontrado(Exception):
    """O livro, leitor ou empréstimo pedido não existe."""


class RegraViolada(Exception):
    """A operação fere uma regra de negócio."""


def realizar_emprestimo(conexao: sqlite3.Connection, livro_id: int, leitor_id: int) -> int:
    # BEGIN IMMEDIATE trava a escrita já aqui. Sem isso, duas requisições
    # simultâneas poderiam ver "1 disponível" e as duas emprestarem o mesmo exemplar.
    conexao.execute("BEGIN IMMEDIATE")

    livro = repositorio.buscar_livro(conexao, livro_id)
    if livro is None:
        raise NaoEncontrado("Livro não encontrado")

    leitor = repositorio.buscar_leitor(conexao, leitor_id)
    if leitor is None:
        raise NaoEncontrado("Leitor não encontrado")

    emprestimos_do_leitor = repositorio.contar_emprestimos_ativos_do_leitor(conexao, leitor_id)
    if emprestimos_do_leitor >= LIMITE_EMPRESTIMOS_ATIVOS:
        raise RegraViolada(
            f"Leitor atingiu o limite de {LIMITE_EMPRESTIMOS_ATIVOS} empréstimos ativos"
        )

    if livro["disponiveis"] <= 0:
        raise RegraViolada("Não há exemplar disponível deste livro")

    data_emprestimo = hoje()
    data_prevista = data_emprestimo + timedelta(days=PRAZO_EMPRESTIMO_DIAS)
    return repositorio.inserir_emprestimo(
        conexao, livro_id, leitor_id, data_emprestimo, data_prevista
    )


def realizar_devolucao(conexao: sqlite3.Connection, emprestimo_id: int) -> float:
    """Registra a devolução e devolve o valor da multa."""
    emprestimo = repositorio.buscar_emprestimo(conexao, emprestimo_id)
    if emprestimo is None:
        raise NaoEncontrado("Empréstimo não encontrado")

    if emprestimo["data_devolucao"] is not None:
        raise RegraViolada("Este empréstimo já foi devolvido")

    data_devolucao = hoje()
    # O SQLite guarda datas como texto "AAAA-MM-DD".
    data_prevista = date.fromisoformat(emprestimo["data_prevista"])
    multa = calcular_multa(data_prevista, data_devolucao)
    repositorio.registrar_devolucao(conexao, emprestimo_id, data_devolucao, multa)
    return multa


def excluir_livro(conexao: sqlite3.Connection, livro_id: int) -> None:
    livro = repositorio.buscar_livro(conexao, livro_id)
    if livro is None:
        raise NaoEncontrado("Livro não encontrado")

    emprestimos_ativos = repositorio.contar_emprestimos_ativos_do_livro(conexao, livro_id)
    if emprestimos_ativos > 0:
        raise RegraViolada("Livro com empréstimo ativo não pode ser excluído")

    repositorio.excluir_livro(conexao, livro_id)
