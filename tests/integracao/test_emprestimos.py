from datetime import date

import pytest

from tests.factories import LeitorFactory, LivroFactory

pytestmark = pytest.mark.integration

# A rota usa "hoje()" importada em app.rotas.emprestimos, então é lá que
# o patch precisa acontecer (no módulo que USA a função, não onde ela nasce).
CAMINHO_DO_HOJE = "app.rotas.emprestimos.hoje"


def emprestar(cliente, livro_id: int, leitor_id: int):
    return cliente.post("/api/emprestimos", json={"livro_id": livro_id, "leitor_id": leitor_id})


def test_emprestar_livro_disponivel_retorna_201(cliente, livro_cadastrado, leitor_cadastrado, mocker):
    # Arrange
    mocker.patch(CAMINHO_DO_HOJE, return_value=date(2026, 11, 1))

    # Act
    resposta = emprestar(cliente, livro_cadastrado["id"], leitor_cadastrado["id"])

    # Assert
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["data_emprestimo"] == "2026-11-01"
    assert corpo["data_prevista"] == "2026-11-15"
    assert corpo["data_devolucao"] is None
    livro_depois = cliente.get(f"/api/livros/{livro_cadastrado['id']}").json()
    assert livro_depois["disponiveis"] == livro_cadastrado["disponiveis"] - 1


def test_emprestar_sem_exemplar_disponivel_retorna_409(cliente):
    # Arrange — um único exemplar, já emprestado para outra pessoa
    livro = cliente.post("/api/livros", json=LivroFactory.criar_dados(quantidade_total=1)).json()
    primeiro_leitor = cliente.post("/api/leitores", json=LeitorFactory.criar_dados()).json()
    segundo_leitor = cliente.post("/api/leitores", json=LeitorFactory.criar_dados()).json()
    emprestar(cliente, livro["id"], primeiro_leitor["id"])

    # Act
    resposta = emprestar(cliente, livro["id"], segundo_leitor["id"])

    # Assert
    assert resposta.status_code == 409
    assert "disponível" in resposta.json()["detail"]


def test_leitor_com_tres_emprestimos_nao_pega_quarto(cliente, leitor_cadastrado):
    # Arrange
    for _ in range(3):
        livro = cliente.post("/api/livros", json=LivroFactory.criar_dados()).json()
        emprestar(cliente, livro["id"], leitor_cadastrado["id"])
    quarto_livro = cliente.post("/api/livros", json=LivroFactory.criar_dados()).json()

    # Act
    resposta = emprestar(cliente, quarto_livro["id"], leitor_cadastrado["id"])

    # Assert
    assert resposta.status_code == 409
    assert "limite" in resposta.json()["detail"]


def test_emprestar_livro_inexistente_retorna_404(cliente, leitor_cadastrado):
    # Act
    resposta = emprestar(cliente, 999, leitor_cadastrado["id"])

    # Assert
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Livro não encontrado"


def test_emprestar_para_leitor_inexistente_retorna_404(cliente, livro_cadastrado):
    # Act
    resposta = emprestar(cliente, livro_cadastrado["id"], 999)

    # Assert
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Leitor não encontrado"


def test_devolucao_no_prazo_multa_zero(cliente, livro_cadastrado, leitor_cadastrado, mocker):
    # Arrange
    falso_hoje = mocker.patch(CAMINHO_DO_HOJE, return_value=date(2026, 11, 1))
    emprestimo = emprestar(cliente, livro_cadastrado["id"], leitor_cadastrado["id"]).json()
    falso_hoje.return_value = date(2026, 11, 15)  # último dia do prazo

    # Act
    resposta = cliente.post(f"/api/emprestimos/{emprestimo['id']}/devolucao")

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["data_devolucao"] == "2026-11-15"
    assert resposta.json()["multa"] == 0


def test_devolucao_com_5_dias_de_atraso_multa_10_reais(
    cliente, livro_cadastrado, leitor_cadastrado, mocker
):
    # Arrange — prazo vence em 15/11; devolvido em 20/11 = 5 dias de atraso
    falso_hoje = mocker.patch(CAMINHO_DO_HOJE, return_value=date(2026, 11, 1))
    emprestimo = emprestar(cliente, livro_cadastrado["id"], leitor_cadastrado["id"]).json()
    falso_hoje.return_value = date(2026, 11, 20)

    # Act
    resposta = cliente.post(f"/api/emprestimos/{emprestimo['id']}/devolucao")

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["multa"] == 10.0


def test_devolver_duas_vezes_retorna_409(cliente, livro_cadastrado, leitor_cadastrado):
    # Arrange
    emprestimo = emprestar(cliente, livro_cadastrado["id"], leitor_cadastrado["id"]).json()
    cliente.post(f"/api/emprestimos/{emprestimo['id']}/devolucao")

    # Act
    resposta = cliente.post(f"/api/emprestimos/{emprestimo['id']}/devolucao")

    # Assert
    assert resposta.status_code == 409


def test_devolver_emprestimo_inexistente_retorna_404(cliente):
    # Act
    resposta = cliente.post("/api/emprestimos/999/devolucao")

    # Assert
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Empréstimo não encontrado"


def test_listar_somente_emprestimos_ativos(cliente, livro_cadastrado, leitor_cadastrado):
    # Arrange — dois empréstimos, um deles devolvido
    primeiro = emprestar(cliente, livro_cadastrado["id"], leitor_cadastrado["id"]).json()
    emprestar(cliente, livro_cadastrado["id"], leitor_cadastrado["id"])
    cliente.post(f"/api/emprestimos/{primeiro['id']}/devolucao")

    # Act
    resposta = cliente.get("/api/emprestimos", params={"ativos": "true"})

    # Assert
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_excluir_livro_com_emprestimo_ativo_retorna_409(cliente, livro_cadastrado, leitor_cadastrado):
    # Arrange
    emprestar(cliente, livro_cadastrado["id"], leitor_cadastrado["id"])

    # Act
    resposta = cliente.delete(f"/api/livros/{livro_cadastrado['id']}")

    # Assert
    assert resposta.status_code == 409


def test_excluir_livro_com_emprestimos_devolvidos_retorna_204(
    cliente, livro_cadastrado, leitor_cadastrado
):
    # Arrange
    emprestimo = emprestar(cliente, livro_cadastrado["id"], leitor_cadastrado["id"]).json()
    cliente.post(f"/api/emprestimos/{emprestimo['id']}/devolucao")

    # Act
    resposta = cliente.delete(f"/api/livros/{livro_cadastrado['id']}")

    # Assert
    assert resposta.status_code == 204


def test_reduzir_quantidade_abaixo_dos_ativos_retorna_409(cliente, livro_cadastrado):
    # Arrange — livro com 2 exemplares, os 2 emprestados
    for _ in range(2):
        leitor = cliente.post("/api/leitores", json=LeitorFactory.criar_dados()).json()
        emprestar(cliente, livro_cadastrado["id"], leitor["id"])
    dados_com_um_exemplar = {
        "isbn": livro_cadastrado["isbn"],
        "titulo": livro_cadastrado["titulo"],
        "autor": livro_cadastrado["autor"],
        "quantidade_total": 1,
    }

    # Act
    resposta = cliente.put(f"/api/livros/{livro_cadastrado['id']}", json=dados_com_um_exemplar)

    # Assert
    assert resposta.status_code == 409
