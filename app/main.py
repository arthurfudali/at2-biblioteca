from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import criar_tabelas
from app.rotas import emprestimos, leitores, livros, paginas


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    criar_tabelas()
    yield


app = FastAPI(title="Biblioteca", lifespan=ciclo_de_vida)
app.include_router(livros.router)
app.include_router(leitores.router)
app.include_router(emprestimos.router)
app.include_router(paginas.router)

PASTA_STATIC = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")
