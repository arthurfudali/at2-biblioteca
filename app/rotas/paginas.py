"""Páginas HTML. Formulários comuns (POST + redirecionamento), sem framework JS."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import repositorio
from app.db import obter_conexao
from app.schemas import LeitorEntrada, LivroEntrada
from app.servicos import biblioteca

PASTA_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=PASTA_TEMPLATES)

router = APIRouter(include_in_schema=False)

NOMES_DOS_CAMPOS = {
    "isbn": "ISBN",
    "titulo": "Título",
    "autor": "Autor",
    "quantidade_total": "Quantidade",
    "nome": "Nome",
    "cpf": "CPF",
    "email": "E-mail",
}

# O Pydantic gera mensagens em inglês; estas são as que o usuário pode provocar.
MENSAGENS_POR_TIPO_DE_ERRO = {
    "missing": "é obrigatório",
    "string_too_short": "está curto demais",
    "string_too_long": "está longo demais",
    "string_pattern_mismatch": "deve ter exatamente 11 dígitos",
    "int_parsing": "deve ser um número inteiro",
    "greater_than_equal": "deve ser pelo menos 1",
    "less_than_equal": "está acima do máximo permitido",
}


def traduzir_erros_de_validacao(erro: ValidationError) -> list[str]:
    mensagens = []
    for problema in erro.errors():
        campo = NOMES_DOS_CAMPOS.get(problema["loc"][0], problema["loc"][0])

        # Erros dos nossos validadores (ex.: ISBN) já vêm em português.
        if problema["type"] == "value_error":
            mensagem_original = str(problema["ctx"]["error"])
            mensagens.append(f"{campo}: {mensagem_original}")
            continue

        mensagem = MENSAGENS_POR_TIPO_DE_ERRO.get(problema["type"], "é inválido")
        mensagens.append(f"{campo} {mensagem}")
    return mensagens


def renderizar(request: Request, template: str, contexto: dict, status_code: int = 200):
    return templates.TemplateResponse(request, template, contexto, status_code=status_code)


# ---------------- Livros ----------------

def pagina_de_livros(request, conexao, erros=None, dados_digitados=None, status_code=200):
    contexto = {
        "livros": repositorio.listar_livros(conexao),
        "erros": erros or [],
        "dados": dados_digitados or {},
    }
    return renderizar(request, "livros.html", contexto, status_code)


@router.get("/", response_class=HTMLResponse)
def livros(request: Request, conexao: sqlite3.Connection = Depends(obter_conexao)):
    return pagina_de_livros(request, conexao)


@router.post("/livros", response_class=HTMLResponse)
async def cadastrar_livro(request: Request, conexao: sqlite3.Connection = Depends(obter_conexao)):
    dados_digitados = dict(await request.form())

    try:
        livro = LivroEntrada(**dados_digitados)
    except ValidationError as erro:
        erros = traduzir_erros_de_validacao(erro)
        return pagina_de_livros(request, conexao, erros, dados_digitados, status_code=422)

    try:
        repositorio.inserir_livro(conexao, livro.model_dump())
    except repositorio.RegistroDuplicado:
        erros = ["Já existe um livro cadastrado com este ISBN"]
        return pagina_de_livros(request, conexao, erros, dados_digitados, status_code=409)

    return RedirectResponse("/", status_code=303)


@router.post("/livros/{livro_id}/excluir", response_class=HTMLResponse)
def excluir_livro(
    request: Request, livro_id: int, conexao: sqlite3.Connection = Depends(obter_conexao)
):
    try:
        biblioteca.excluir_livro(conexao, livro_id)
    except (biblioteca.NaoEncontrado, biblioteca.RegraViolada) as erro:
        return pagina_de_livros(request, conexao, [str(erro)], status_code=409)

    return RedirectResponse("/", status_code=303)


# ---------------- Leitores ----------------

def pagina_de_leitores(request, conexao, erros=None, dados_digitados=None, status_code=200):
    contexto = {
        "leitores": repositorio.listar_leitores(conexao),
        "erros": erros or [],
        "dados": dados_digitados or {},
    }
    return renderizar(request, "leitores.html", contexto, status_code)


@router.get("/leitores", response_class=HTMLResponse)
def leitores(request: Request, conexao: sqlite3.Connection = Depends(obter_conexao)):
    return pagina_de_leitores(request, conexao)


@router.post("/leitores", response_class=HTMLResponse)
async def cadastrar_leitor(request: Request, conexao: sqlite3.Connection = Depends(obter_conexao)):
    dados_digitados = dict(await request.form())

    try:
        leitor = LeitorEntrada(**dados_digitados)
    except ValidationError as erro:
        erros = traduzir_erros_de_validacao(erro)
        return pagina_de_leitores(request, conexao, erros, dados_digitados, status_code=422)

    try:
        repositorio.inserir_leitor(conexao, leitor.model_dump())
    except repositorio.RegistroDuplicado:
        erros = ["Já existe um leitor com este CPF"]
        return pagina_de_leitores(request, conexao, erros, dados_digitados, status_code=409)

    return RedirectResponse("/leitores", status_code=303)


# ---------------- Empréstimos ----------------

def pagina_de_emprestimos(request, conexao, erros=None, aviso=None, status_code=200):
    contexto = {
        "livros": repositorio.listar_livros(conexao),
        "leitores": repositorio.listar_leitores(conexao),
        "emprestimos_ativos": repositorio.listar_emprestimos(conexao, somente_ativos=True),
        "erros": erros or [],
        "aviso": aviso,
    }
    return renderizar(request, "emprestimos.html", contexto, status_code)


@router.get("/emprestimos", response_class=HTMLResponse)
def emprestimos(
    request: Request, multa: float | None = None,
    conexao: sqlite3.Connection = Depends(obter_conexao),
):
    aviso = None
    if multa is not None:
        valor_formatado = f"{multa:.2f}".replace(".", ",")
        aviso = f"Devolução registrada. Multa: R$ {valor_formatado}"
    return pagina_de_emprestimos(request, conexao, aviso=aviso)


@router.post("/emprestimos", response_class=HTMLResponse)
async def emprestar(request: Request, conexao: sqlite3.Connection = Depends(obter_conexao)):
    formulario = await request.form()

    try:
        livro_id = int(formulario["livro_id"])
        leitor_id = int(formulario["leitor_id"])
    except (KeyError, ValueError):
        erros = ["Selecione um livro e um leitor"]
        return pagina_de_emprestimos(request, conexao, erros, status_code=422)

    try:
        biblioteca.realizar_emprestimo(conexao, livro_id, leitor_id)
    except (biblioteca.NaoEncontrado, biblioteca.RegraViolada) as erro:
        # O BEGIN IMMEDIATE do serviço deixou uma transação aberta; desfaz
        # antes de consultar de novo para montar a página com o erro.
        conexao.rollback()
        return pagina_de_emprestimos(request, conexao, [str(erro)], status_code=409)

    return RedirectResponse("/emprestimos", status_code=303)


@router.post("/emprestimos/{emprestimo_id}/devolver", response_class=HTMLResponse)
def devolver(
    request: Request, emprestimo_id: int, conexao: sqlite3.Connection = Depends(obter_conexao)
):
    try:
        multa = biblioteca.realizar_devolucao(conexao, emprestimo_id)
    except (biblioteca.NaoEncontrado, biblioteca.RegraViolada) as erro:
        return pagina_de_emprestimos(request, conexao, [str(erro)], status_code=409)

    return RedirectResponse(f"/emprestimos?multa={multa}", status_code=303)
