from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import criar_tabelas
from app.rotas import leitores, livros


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    criar_tabelas()
    yield


app = FastAPI(title="Biblioteca", lifespan=ciclo_de_vida)
app.include_router(livros.router)
app.include_router(leitores.router)
