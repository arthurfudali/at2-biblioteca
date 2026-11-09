import pytest

from tests.factories import LeitorFactory

pytestmark = pytest.mark.integration


def test_cadastrar_leitor_valido_retorna_201(cliente):
    # Arrange
    dados_do_leitor = LeitorFactory.criar_dados()

    # Act
    resposta = cliente.post("/api/leitores", json=dados_do_leitor)

    # Assert
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] > 0
    assert corpo["nome"] == dados_do_leitor["nome"]
    assert corpo["cpf"] == dados_do_leitor["cpf"]


def test_cadastrar_leitor_email_invalido_retorna_422(cliente):
    # Arrange
    dados_do_leitor = LeitorFactory.criar_dados(email="nao-e-um-email")

    # Act
    resposta = cliente.post("/api/leitores", json=dados_do_leitor)

    # Assert
    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["loc"] == ["body", "email"]


def test_cadastrar_leitor_cpf_com_letras_retorna_422(cliente):
    # Arrange
    dados_do_leitor = LeitorFactory.criar_dados(cpf="123abc78901")

    # Act
    resposta = cliente.post("/api/leitores", json=dados_do_leitor)

    # Assert
    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["loc"] == ["body", "cpf"]


def test_cadastrar_leitor_cpf_duplicado_retorna_409(cliente):
    # Arrange
    primeiro_leitor = LeitorFactory.criar_dados()
    cliente.post("/api/leitores", json=primeiro_leitor)
    leitor_com_mesmo_cpf = LeitorFactory.criar_dados(cpf=primeiro_leitor["cpf"])

    # Act
    resposta = cliente.post("/api/leitores", json=leitor_com_mesmo_cpf)

    # Assert
    assert resposta.status_code == 409
    assert "CPF" in resposta.json()["detail"]


def test_listar_leitores(cliente):
    # Arrange
    cliente.post("/api/leitores", json=LeitorFactory.criar_dados())

    # Act
    resposta = cliente.get("/api/leitores")

    # Assert
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
