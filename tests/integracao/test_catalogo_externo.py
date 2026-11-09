"""Testes da integração com a OpenLibrary.

A API real nunca é chamada: a rede deixaria os testes lentos e instáveis
(fora do ar, limite de requisições, dados que mudam). Em vez disso,
mocker.patch troca a função ou o httpx por um dublê com a resposta que
cada cenário precisa.
"""

from unittest.mock import Mock

import httpx
import pytest

from app.servicos.catalogo_externo import CatalogoIndisponivel, buscar_dados_do_livro

pytestmark = pytest.mark.integration

ISBN_VALIDO = "9788535902778"


# ---- Rota /api/livros/preencher/{isbn}: o serviço inteiro é mockado ----

def test_preencher_isbn_sucesso_retorna_dados_do_catalogo(cliente, mocker):
    # Arrange
    falso_catalogo = mocker.patch(
        "app.rotas.livros.buscar_dados_do_livro",
        return_value={"titulo": "Dom Casmurro", "autor": "Machado de Assis"},
    )

    # Act
    resposta = cliente.get(f"/api/livros/preencher/{ISBN_VALIDO}")

    # Assert
    assert resposta.status_code == 200
    assert resposta.json() == {"titulo": "Dom Casmurro", "autor": "Machado de Assis"}
    falso_catalogo.assert_called_once_with(ISBN_VALIDO)


def test_preencher_isbn_nao_encontrado_retorna_404(cliente, mocker):
    # Arrange
    mocker.patch("app.rotas.livros.buscar_dados_do_livro", return_value=None)

    # Act
    resposta = cliente.get(f"/api/livros/preencher/{ISBN_VALIDO}")

    # Assert
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "ISBN não encontrado no catálogo"


def test_preencher_catalogo_fora_do_ar_retorna_503(cliente, mocker):
    # Arrange
    mocker.patch(
        "app.rotas.livros.buscar_dados_do_livro",
        side_effect=CatalogoIndisponivel("timeout"),
    )

    # Act
    resposta = cliente.get(f"/api/livros/preencher/{ISBN_VALIDO}")

    # Assert
    assert resposta.status_code == 503
    assert "manualmente" in resposta.json()["detail"]


def test_cadastro_manual_funciona_com_catalogo_fora_do_ar(cliente, mocker):
    # Arrange — mesmo com a API externa caída, cadastrar não depende dela
    mocker.patch(
        "app.rotas.livros.buscar_dados_do_livro",
        side_effect=CatalogoIndisponivel("timeout"),
    )
    dados = {"isbn": ISBN_VALIDO, "titulo": "Dom Casmurro", "autor": "Machado de Assis",
             "quantidade_total": 1}

    # Act
    resposta = cliente.post("/api/livros", json=dados)

    # Assert
    assert resposta.status_code == 201


def test_preencher_com_isbn_invalido_retorna_422_sem_chamar_catalogo(cliente, mocker):
    # Arrange
    falso_catalogo = mocker.patch("app.rotas.livros.buscar_dados_do_livro")

    # Act
    resposta = cliente.get("/api/livros/preencher/123")

    # Assert
    assert resposta.status_code == 422
    falso_catalogo.assert_not_called()


# ---- Serviço buscar_dados_do_livro: o httpx é mockado ----

def criar_resposta_falsa(status_code: int, corpo: dict) -> Mock:
    resposta = Mock()
    resposta.status_code = status_code
    resposta.json.return_value = corpo
    return resposta


def test_buscar_dados_converte_resposta_da_openlibrary(mocker):
    # Arrange — a OpenLibrary devolve o autor só como chave; o nome vem numa 2ª chamada
    resposta_do_livro = criar_resposta_falsa(
        200, {"title": "Dom Casmurro", "authors": [{"key": "/authors/OL123A"}]}
    )
    resposta_do_autor = criar_resposta_falsa(200, {"name": "Machado de Assis"})
    falso_get = mocker.patch(
        "app.servicos.catalogo_externo.httpx.get",
        side_effect=[resposta_do_livro, resposta_do_autor],
    )

    # Act
    dados = buscar_dados_do_livro(ISBN_VALIDO)

    # Assert
    assert dados == {"titulo": "Dom Casmurro", "autor": "Machado de Assis"}
    assert falso_get.call_count == 2


def test_buscar_dados_isbn_inexistente_retorna_none(mocker):
    # Arrange
    mocker.patch(
        "app.servicos.catalogo_externo.httpx.get",
        return_value=criar_resposta_falsa(404, {}),
    )

    # Act
    dados = buscar_dados_do_livro(ISBN_VALIDO)

    # Assert
    assert dados is None


def test_buscar_dados_timeout_vira_catalogo_indisponivel(mocker):
    # Arrange
    mocker.patch(
        "app.servicos.catalogo_externo.httpx.get",
        side_effect=httpx.TimeoutException("demorou demais"),
    )

    # Act / Assert
    with pytest.raises(CatalogoIndisponivel):
        buscar_dados_do_livro(ISBN_VALIDO)


def test_buscar_dados_erro_500_vira_catalogo_indisponivel(mocker):
    # Arrange
    mocker.patch(
        "app.servicos.catalogo_externo.httpx.get",
        return_value=criar_resposta_falsa(500, {}),
    )

    # Act / Assert
    with pytest.raises(CatalogoIndisponivel):
        buscar_dados_do_livro(ISBN_VALIDO)
