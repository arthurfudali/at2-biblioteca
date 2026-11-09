from fastapi import APIRouter, HTTPException

from app import repositorio
from app.db import Conexao
from app.schemas import EmprestimoEntrada, EmprestimoSaida
from app.servicos.biblioteca import (
    NaoEncontrado,
    RegraViolada,
    realizar_devolucao,
    realizar_emprestimo,
)

router = APIRouter(prefix="/api/emprestimos", tags=["emprestimos"])


@router.get("", response_model=list[EmprestimoSaida])
def listar(conexao: Conexao, ativos: bool = False):
    return repositorio.listar_emprestimos(conexao, somente_ativos=ativos)


@router.post("", response_model=EmprestimoSaida, status_code=201)
def emprestar(pedido: EmprestimoEntrada, conexao: Conexao):
    try:
        emprestimo_id = realizar_emprestimo(conexao, pedido.livro_id, pedido.leitor_id)
    except NaoEncontrado as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except RegraViolada as erro:
        raise HTTPException(status_code=409, detail=str(erro))
    return repositorio.buscar_emprestimo(conexao, emprestimo_id)


@router.post("/{emprestimo_id}/devolucao", response_model=EmprestimoSaida)
def devolver(emprestimo_id: int, conexao: Conexao):
    try:
        realizar_devolucao(conexao, emprestimo_id)
    except NaoEncontrado as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except RegraViolada as erro:
        raise HTTPException(status_code=409, detail=str(erro))
    return repositorio.buscar_emprestimo(conexao, emprestimo_id)
