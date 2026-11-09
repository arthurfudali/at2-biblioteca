import os
import socket
import subprocess
import sys
import time

import httpx
import pytest


def encontrar_porta_livre() -> int:
    # Porta 0 = "sistema operacional, escolha uma livre"; assim os testes não
    # brigam com um servidor que o Arthur esteja rodando na 8000.
    with socket.socket() as soquete:
        soquete.bind(("127.0.0.1", 0))
        return soquete.getsockname()[1]


def esperar_servidor_responder(url: str, tempo_maximo_segundos: float = 15) -> None:
    limite = time.monotonic() + tempo_maximo_segundos
    while time.monotonic() < limite:
        try:
            httpx.get(url, timeout=1)
            return
        except httpx.HTTPError:
            time.sleep(0.2)
    raise RuntimeError(f"Servidor não respondeu em {url}")


@pytest.fixture(scope="session")
def url_base(tmp_path_factory):
    """Sobe o app de verdade (uvicorn) com um banco vazio, uma vez por sessão."""
    porta = encontrar_porta_livre()
    caminho_do_banco = tmp_path_factory.mktemp("e2e") / "e2e.db"
    ambiente = {**os.environ, "BIBLIOTECA_DB": str(caminho_do_banco)}

    servidor = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(porta)],
        env=ambiente,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{porta}"
    esperar_servidor_responder(url)

    yield url

    servidor.terminate()
    servidor.wait(timeout=10)


@pytest.fixture
def api(url_base):
    """Cliente HTTP para preparar dados (Arrange) sem passar pela interface."""
    with httpx.Client(base_url=url_base) as cliente:
        yield cliente
