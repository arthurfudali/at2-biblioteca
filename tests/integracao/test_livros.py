import pytest

from tests.factories import LivroFactory

pytestmark = pytest.mark.integration


def test_cadastrar_livro_valido_retorna_201(cliente):
    # Arrange
    dados_do_livro = LivroFactory.criar_dados(quantidade_total=3)

    # Act
    resposta = cliente.post("/api/livros", json=dados_do_livro)

    # Assert
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] > 0
    assert corpo["isbn"] == dados_do_livro["isbn"]
    assert corpo["titulo"] == dados_do_livro["titulo"]
    assert corpo["disponiveis"] == 3


def test_cadastrar_livro_com_isbn_invalido_retorna_422(cliente):
    # Arrange — último dígito errado (o correto seria 8)
    dados_do_livro = LivroFactory.criar_dados(isbn="9788535902779")

    # Act
    resposta = cliente.post("/api/livros", json=dados_do_livro)

    # Assert
    assert resposta.status_code == 422
    erro = resposta.json()["detail"][0]
    assert erro["loc"] == ["body", "isbn"]
    assert "ISBN-13 inválido" in erro["msg"]


def test_cadastrar_isbn_com_hifens_e_normalizado(cliente):
    # Arrange
    dados_do_livro = LivroFactory.criar_dados(isbn="978-85-359-0277-8")

    # Act
    resposta = cliente.post("/api/livros", json=dados_do_livro)

    # Assert
    assert resposta.status_code == 201
    assert resposta.json()["isbn"] == "9788535902778"


def test_cadastrar_isbn_com_espacos_e_normalizado(cliente):
    # Arrange
    dados_do_livro = LivroFactory.criar_dados(isbn="978 85 359 0277 8")

    # Act
    resposta = cliente.post("/api/livros", json=dados_do_livro)

    # Assert
    assert resposta.status_code == 201
    assert resposta.json()["isbn"] == "9788535902778"


def test_cadastrar_isbn_duplicado_retorna_409(cliente):
    # Arrange
    primeiro_livro = LivroFactory.criar_dados()
    cliente.post("/api/livros", json=primeiro_livro)
    livro_com_mesmo_isbn = LivroFactory.criar_dados(isbn=primeiro_livro["isbn"])

    # Act
    resposta = cliente.post("/api/livros", json=livro_com_mesmo_isbn)

    # Assert
    assert resposta.status_code == 409
    assert "ISBN" in resposta.json()["detail"]


def test_listar_livros_retorna_cadastrados(cliente):
    # Arrange
    cliente.post("/api/livros", json=LivroFactory.criar_dados())
    cliente.post("/api/livros", json=LivroFactory.criar_dados())

    # Act
    resposta = cliente.get("/api/livros")

    # Assert
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_buscar_livro_inexistente_retorna_404(cliente):
    # Act
    resposta = cliente.get("/api/livros/999")

    # Assert
    assert resposta.status_code == 404


def test_atualizar_livro_altera_titulo(cliente):
    # Arrange
    dados_do_livro = LivroFactory.criar_dados()
    livro_id = cliente.post("/api/livros", json=dados_do_livro).json()["id"]
    dados_atualizados = {**dados_do_livro, "titulo": "Título Novo"}

    # Act
    resposta = cliente.put(f"/api/livros/{livro_id}", json=dados_atualizados)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["titulo"] == "Título Novo"


def test_excluir_livro_sem_emprestimo_retorna_204(cliente):
    # Arrange
    livro_id = cliente.post("/api/livros", json=LivroFactory.criar_dados()).json()["id"]

    # Act
    resposta = cliente.delete(f"/api/livros/{livro_id}")

    # Assert
    assert resposta.status_code == 204
    assert cliente.get(f"/api/livros/{livro_id}").status_code == 404
