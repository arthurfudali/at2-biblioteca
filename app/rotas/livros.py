import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response

from app import repositorio
from app.db import obter_conexao
from app.isbn import isbn13_valido, normalizar_isbn
from app.schemas import LivroEntrada, LivroSaida
from app.servicos.catalogo_externo import CatalogoIndisponivel, buscar_dados_do_livro

router = APIRouter(prefix="/api/livros", tags=["livros"])

MENSAGEM_ISBN_DUPLICADO = "Já existe um livro cadastrado com este ISBN"


def buscar_livro_ou_404(conexao: sqlite3.Connection, livro_id: int) -> dict:
    livro = repositorio.buscar_livro(conexao, livro_id)
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    return livro


@router.get("", response_model=list[LivroSaida])
def listar(conexao: sqlite3.Connection = Depends(obter_conexao)):
    return repositorio.listar_livros(conexao)


@router.post("", response_model=LivroSaida, status_code=201)
def cadastrar(livro: LivroEntrada, conexao: sqlite3.Connection = Depends(obter_conexao)):
    try:
        livro_id = repositorio.inserir_livro(conexao, livro.model_dump())
    except repositorio.RegistroDuplicado:
        raise HTTPException(status_code=409, detail=MENSAGEM_ISBN_DUPLICADO)
    return repositorio.buscar_livro(conexao, livro_id)


@router.get("/{livro_id}", response_model=LivroSaida)
def buscar(livro_id: int, conexao: sqlite3.Connection = Depends(obter_conexao)):
    return buscar_livro_ou_404(conexao, livro_id)


@router.put("/{livro_id}", response_model=LivroSaida)
def atualizar(
    livro_id: int, livro: LivroEntrada, conexao: sqlite3.Connection = Depends(obter_conexao)
):
    buscar_livro_ou_404(conexao, livro_id)

    emprestimos_ativos = repositorio.contar_emprestimos_ativos_do_livro(conexao, livro_id)
    if livro.quantidade_total < emprestimos_ativos:
        raise HTTPException(
            status_code=409,
            detail=f"Há {emprestimos_ativos} exemplares emprestados; a quantidade não pode ser menor",
        )

    try:
        repositorio.atualizar_livro(conexao, livro_id, livro.model_dump())
    except repositorio.RegistroDuplicado:
        raise HTTPException(status_code=409, detail=MENSAGEM_ISBN_DUPLICADO)
    return repositorio.buscar_livro(conexao, livro_id)


@router.delete("/{livro_id}", status_code=204)
def excluir(livro_id: int, conexao: sqlite3.Connection = Depends(obter_conexao)):
    buscar_livro_ou_404(conexao, livro_id)

    emprestimos_ativos = repositorio.contar_emprestimos_ativos_do_livro(conexao, livro_id)
    if emprestimos_ativos > 0:
        raise HTTPException(
            status_code=409, detail="Livro com empréstimo ativo não pode ser excluído"
        )

    repositorio.excluir_livro(conexao, livro_id)
    return Response(status_code=204)


@router.get("/preencher/{isbn}")
def preencher_pelo_isbn(isbn: str):
    """Sugere título e autor consultando a OpenLibrary. Não grava nada."""
    isbn = normalizar_isbn(isbn)
    if not isbn13_valido(isbn):
        raise HTTPException(status_code=422, detail="ISBN-13 inválido")

    try:
        dados = buscar_dados_do_livro(isbn)
    except CatalogoIndisponivel:
        raise HTTPException(
            status_code=503, detail="Catálogo externo indisponível, preencha manualmente"
        )

    if dados is None:
        raise HTTPException(status_code=404, detail="ISBN não encontrado no catálogo")
    return dados
