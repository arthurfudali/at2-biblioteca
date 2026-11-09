import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages.emprestimos_page import EmprestimosPage
from tests.e2e.pages.leitores_page import LeitoresPage
from tests.e2e.pages.livros_page import LivrosPage
from tests.factories import LeitorFactory, LivroFactory

pytestmark = pytest.mark.e2e


def test_cadastrar_livro_aparece_na_tabela(page: Page, url_base):
    # Arrange
    livro = LivroFactory.criar_dados(quantidade_total=2)
    pagina_de_livros = LivrosPage(page, url_base)
    pagina_de_livros.abrir()

    # Act
    pagina_de_livros.cadastrar(livro["isbn"], livro["titulo"], livro["autor"], 2)

    # Assert
    linha = pagina_de_livros.linha_do_livro(livro["titulo"])
    expect(linha).to_be_visible()
    expect(linha).to_contain_text("2 de 2")


def test_cadastrar_livro_com_isbn_invalido_mostra_erro(page: Page, url_base):
    # Arrange
    livro = LivroFactory.criar_dados()
    pagina_de_livros = LivrosPage(page, url_base)
    pagina_de_livros.abrir()

    # Act
    pagina_de_livros.cadastrar("9788535902779", livro["titulo"], livro["autor"], 1)

    # Assert
    expect(pagina_de_livros.mensagem_de_erro).to_contain_text("ISBN-13 inválido")
    expect(pagina_de_livros.linha_do_livro(livro["titulo"])).to_have_count(0)


def test_fluxo_completo_emprestar_e_devolver(page: Page, url_base):
    # Arrange — cadastros feitos pela própria interface
    livro = LivroFactory.criar_dados()
    leitor = LeitorFactory.criar_dados()

    pagina_de_livros = LivrosPage(page, url_base)
    pagina_de_livros.abrir()
    pagina_de_livros.cadastrar(livro["isbn"], livro["titulo"], livro["autor"], 1)

    pagina_de_leitores = LeitoresPage(page, url_base)
    pagina_de_leitores.abrir()
    pagina_de_leitores.cadastrar(leitor["nome"], leitor["cpf"], leitor["email"])

    pagina_de_emprestimos = EmprestimosPage(page, url_base)
    pagina_de_emprestimos.abrir()

    # Act 1 — emprestar
    pagina_de_emprestimos.emprestar(livro["titulo"], leitor["nome"])

    # Assert 1
    linha = pagina_de_emprestimos.linha_do_emprestimo(livro["titulo"])
    expect(linha).to_contain_text(leitor["nome"])

    # Act 2 — devolver no mesmo dia
    pagina_de_emprestimos.devolver(livro["titulo"], leitor["nome"])

    # Assert 2
    expect(pagina_de_emprestimos.aviso).to_have_text("Devolução registrada. Multa: R$ 0,00")
    expect(linha).to_have_count(0)


def test_emprestar_livro_esgotado_mostra_erro(page: Page, url_base, api):
    # Arrange — via API: livro com 1 exemplar, já emprestado para outro leitor
    livro = api.post("/api/livros", json=LivroFactory.criar_dados(quantidade_total=1)).json()
    primeiro_leitor = api.post("/api/leitores", json=LeitorFactory.criar_dados()).json()
    segundo_leitor = api.post("/api/leitores", json=LeitorFactory.criar_dados()).json()
    api.post("/api/emprestimos", json={"livro_id": livro["id"], "leitor_id": primeiro_leitor["id"]})

    pagina_de_emprestimos = EmprestimosPage(page, url_base)
    pagina_de_emprestimos.abrir()

    # Act
    pagina_de_emprestimos.emprestar(livro["titulo"], segundo_leitor["nome"])

    # Assert
    expect(pagina_de_emprestimos.mensagem_de_erro).to_have_text(
        "Não há exemplar disponível deste livro"
    )
