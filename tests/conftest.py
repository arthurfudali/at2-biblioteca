import pytest
from fastapi.testclient import TestClient

from app.main import app


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
