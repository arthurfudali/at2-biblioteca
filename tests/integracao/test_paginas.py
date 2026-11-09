import pytest

from tests.factories import LeitorFactory, LivroFactory

pytestmark = pytest.mark.integration


def test_pagina_livros_retorna_html(cliente):
    # Arrange
    livro = LivroFactory.criar_dados()
    cliente.post("/api/livros", json=livro)

    # Act
    resposta = cliente.get("/")

    # Assert
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]
    assert livro["titulo"] in resposta.text


def test_formulario_de_livro_cadastra_e_redireciona(cliente):
    # Arrange
    livro = LivroFactory.criar_dados()

    # Act
    resposta = cliente.post("/livros", data=livro, follow_redirects=False)

    # Assert
    assert resposta.status_code == 303
    assert livro["titulo"] in cliente.get("/").text


def test_formulario_de_livro_com_isbn_invalido_mostra_erro(cliente):
    # Arrange
    livro = LivroFactory.criar_dados(isbn="123")

    # Act
    resposta = cliente.post("/livros", data=livro)

    # Assert
    assert resposta.status_code == 422
    assert "ISBN-13 inválido" in resposta.text


def test_pagina_emprestimos_lista_ativos(cliente):
    # Arrange
    livro = cliente.post("/api/livros", json=LivroFactory.criar_dados()).json()
    leitor = cliente.post("/api/leitores", json=LeitorFactory.criar_dados()).json()
    cliente.post("/api/emprestimos", json={"livro_id": livro["id"], "leitor_id": leitor["id"]})

    # Act
    resposta = cliente.get("/emprestimos")

    # Assert
    assert resposta.status_code == 200
    assert leitor["nome"] in resposta.text


def test_formulario_de_emprestimo_sem_exemplar_mostra_erro(cliente):
    # Arrange
    livro = cliente.post("/api/livros", json=LivroFactory.criar_dados(quantidade_total=1)).json()
    primeiro = cliente.post("/api/leitores", json=LeitorFactory.criar_dados()).json()
    segundo = cliente.post("/api/leitores", json=LeitorFactory.criar_dados()).json()
    cliente.post("/emprestimos", data={"livro_id": livro["id"], "leitor_id": primeiro["id"]})

    # Act
    resposta = cliente.post(
        "/emprestimos", data={"livro_id": livro["id"], "leitor_id": segundo["id"]}
    )

    # Assert
    assert resposta.status_code == 409
    assert "Não há exemplar disponível" in resposta.text


def test_pagina_leitores_cadastra_pelo_formulario(cliente):
    # Arrange
    leitor = LeitorFactory.criar_dados()

    # Act
    cliente.post("/leitores", data=leitor)

    # Assert
    assert leitor["nome"] in cliente.get("/leitores").text
