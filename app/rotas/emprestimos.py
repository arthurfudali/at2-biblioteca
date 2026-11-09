import sqlite3
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException

from app import repositorio
from app.datas import hoje
from app.db import obter_conexao
from app.regras import LIMITE_EMPRESTIMOS_ATIVOS, PRAZO_EMPRESTIMO_DIAS, calcular_multa
from app.schemas import EmprestimoEntrada, EmprestimoSaida

router = APIRouter(prefix="/api/emprestimos", tags=["emprestimos"])


class RegraViolada(Exception):
    """Erro de regra de negócio; as rotas da API viram 409, as páginas mostram a mensagem."""


def realizar_emprestimo(conexao: sqlite3.Connection, livro_id: int, leitor_id: int) -> int:
    # BEGIN IMMEDIATE trava a escrita já aqui. Sem isso, duas requisições
    # simultâneas poderiam ver "1 disponível" e as duas emprestarem o mesmo exemplar.
    conexao.execute("BEGIN IMMEDIATE")

    livro = repositorio.buscar_livro(conexao, livro_id)
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado")

    leitor = repositorio.buscar_leitor(conexao, leitor_id)
    if leitor is None:
        raise HTTPException(status_code=404, detail="Leitor não encontrado")

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


def realizar_devolucao(conexao: sqlite3.Connection, emprestimo_id: int) -> None:
    emprestimo = repositorio.buscar_emprestimo(conexao, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")

    if emprestimo["data_devolucao"] is not None:
        raise RegraViolada("Este empréstimo já foi devolvido")

    data_devolucao = hoje()
    # O SQLite guarda datas como texto "AAAA-MM-DD".
    data_prevista = date.fromisoformat(emprestimo["data_prevista"])
    multa = calcular_multa(data_prevista, data_devolucao)
    repositorio.registrar_devolucao(conexao, emprestimo_id, data_devolucao, multa)


@router.get("", response_model=list[EmprestimoSaida])
def listar(ativos: bool = False, conexao: sqlite3.Connection = Depends(obter_conexao)):
    return repositorio.listar_emprestimos(conexao, somente_ativos=ativos)


@router.post("", response_model=EmprestimoSaida, status_code=201)
def emprestar(pedido: EmprestimoEntrada, conexao: sqlite3.Connection = Depends(obter_conexao)):
    try:
        emprestimo_id = realizar_emprestimo(conexao, pedido.livro_id, pedido.leitor_id)
    except RegraViolada as erro:
        raise HTTPException(status_code=409, detail=str(erro))
    return repositorio.buscar_emprestimo(conexao, emprestimo_id)


@router.post("/{emprestimo_id}/devolucao", response_model=EmprestimoSaida)
def devolver(emprestimo_id: int, conexao: sqlite3.Connection = Depends(obter_conexao)):
    try:
        realizar_devolucao(conexao, emprestimo_id)
    except RegraViolada as erro:
        raise HTTPException(status_code=409, detail=str(erro))
    return repositorio.buscar_emprestimo(conexao, emprestimo_id)
