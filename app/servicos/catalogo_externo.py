"""Consulta à OpenLibrary para sugerir título e autor a partir do ISBN.

É a única dependência externa do sistema. Fica isolada neste módulo para
que os testes troquem a rede por um mock e para que uma falha aqui nunca
impeça o cadastro manual.
"""

import httpx

URL_BASE = "https://openlibrary.org"
TEMPO_LIMITE_SEGUNDOS = 5


class CatalogoIndisponivel(Exception):
    """A OpenLibrary não respondeu ou respondeu com erro."""


def consultar(caminho: str) -> httpx.Response:
    try:
        return httpx.get(URL_BASE + caminho, timeout=TEMPO_LIMITE_SEGUNDOS, follow_redirects=True)
    except httpx.HTTPError as erro:
        raise CatalogoIndisponivel(str(erro)) from erro


def buscar_nome_do_autor(dados_do_livro: dict) -> str:
    # A OpenLibrary devolve o autor só como chave ("/authors/OL123A");
    # o nome exige uma segunda chamada.
    autores = dados_do_livro.get("authors", [])
    if not autores:
        return ""

    resposta = consultar(autores[0]["key"] + ".json")
    if resposta.status_code != 200:
        return ""
    return resposta.json().get("name", "")


def buscar_dados_do_livro(isbn: str) -> dict | None:
    """Devolve {"titulo", "autor"}; None se o ISBN não existe no catálogo."""
    resposta = consultar(f"/isbn/{isbn}.json")

    if resposta.status_code == 404:
        return None
    if resposta.status_code != 200:
        raise CatalogoIndisponivel(f"OpenLibrary respondeu {resposta.status_code}")

    dados_do_livro = resposta.json()
    return {
        "titulo": dados_do_livro.get("title", ""),
        "autor": buscar_nome_do_autor(dados_do_livro),
    }
