from fastapi import APIRouter, HTTPException

from app import repositorio
from app.db import Conexao
from app.schemas import LeitorEntrada, LeitorSaida

router = APIRouter(prefix="/api/leitores", tags=["leitores"])


@router.get("", response_model=list[LeitorSaida])
def listar(conexao: Conexao):
    return repositorio.listar_leitores(conexao)


@router.post("", response_model=LeitorSaida, status_code=201)
def cadastrar(leitor: LeitorEntrada, conexao: Conexao):
    try:
        leitor_id = repositorio.inserir_leitor(conexao, leitor.model_dump())
    except repositorio.RegistroDuplicado:
        raise HTTPException(status_code=409, detail="Já existe um leitor com este CPF")
    return repositorio.buscar_leitor(conexao, leitor_id)


@router.get("/{leitor_id}", response_model=LeitorSaida)
def buscar(leitor_id: int, conexao: Conexao):
    leitor = repositorio.buscar_leitor(conexao, leitor_id)
    if leitor is None:
        raise HTTPException(status_code=404, detail="Leitor não encontrado")
    return leitor
