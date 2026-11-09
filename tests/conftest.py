import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.factories import LeitorFactory, LivroFactory


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    # Setup: cada teste ganha um banco SQLite novo num diretório temporário,
    # então nenhum teste enxerga dados de outro.
    caminho_do_banco = tmp_path / "teste.db"
    monkeypatch.setenv("BIBLIOTECA_DB", str(caminho_do_banco))

    # O "with" dispara o lifespan do FastAPI, que cria as tabelas.
    with TestClient(app) as cliente_de_teste:
        yield cliente_de_teste

    # Teardown: roda depois do teste, mesmo se ele falhar.
    caminho_do_banco.unlink(missing_ok=True)


@pytest.fixture
def livro_cadastrado(cliente):
    resposta = cliente.post("/api/livros", json=LivroFactory.criar_dados(quantidade_total=2))
    return resposta.json()


@pytest.fixture
def leitor_cadastrado(cliente):
    resposta = cliente.post("/api/leitores", json=LeitorFactory.criar_dados())
    return resposta.json()
