"""Auditoria WCAG 2.1 nível AA com Axe-core e navegação por teclado."""

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page, expect

from tests.e2e.pages.livros_page import LivrosPage
from tests.factories import LeitorFactory, LivroFactory

pytestmark = pytest.mark.accessibility

# Só as regras dos níveis A e AA das WCAG 2.0 e 2.1 (AA inclui o A).
REGRAS_WCAG_21_AA = {
    "runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]}
}


@pytest.fixture
def dados_nas_tabelas(api):
    # Sem dados, as tabelas nem aparecem e o Axe não as audita.
    livro = api.post("/api/livros", json=LivroFactory.criar_dados()).json()
    leitor = api.post("/api/leitores", json=LeitorFactory.criar_dados()).json()
    api.post("/api/emprestimos", json={"livro_id": livro["id"], "leitor_id": leitor["id"]})


@pytest.mark.parametrize("caminho", ["/", "/leitores", "/emprestimos"])
def test_pagina_sem_violacoes_wcag_aa(page: Page, url_base, dados_nas_tabelas, caminho):
    # Arrange
    page.goto(url_base + caminho)

    # Act
    resultado = Axe().run(page, options=REGRAS_WCAG_21_AA)

    # Assert — o relatório só aparece se falhar, listando cada violação
    assert resultado.violations_count == 0, resultado.generate_report()


def test_pagina_com_mensagem_de_erro_sem_violacoes(page: Page, url_base):
    # Arrange — o estado de erro também precisa ser acessível
    pagina_de_livros = LivrosPage(page, url_base)
    pagina_de_livros.abrir()
    pagina_de_livros.cadastrar("123", "Qualquer", "Qualquer", 1)
    expect(pagina_de_livros.mensagem_de_erro).to_be_visible()

    # Act
    resultado = Axe().run(page, options=REGRAS_WCAG_21_AA)

    # Assert
    assert resultado.violations_count == 0, resultado.generate_report()


def test_navegacao_por_tab_no_formulario_de_livro(page: Page, url_base):
    # Arrange
    pagina_de_livros = LivrosPage(page, url_base)
    pagina_de_livros.abrir()
    navegacao = page.get_by_role("navigation", name="Principal")
    ordem_esperada = [
        page.get_by_role("link", name="Pular para o conteúdo"),
        navegacao.get_by_role("link", name="Livros"),
        navegacao.get_by_role("link", name="Leitores"),
        navegacao.get_by_role("link", name="Empréstimos"),
        pagina_de_livros.campo_isbn,
        pagina_de_livros.botao_buscar_isbn,
        pagina_de_livros.campo_titulo,
        pagina_de_livros.campo_autor,
        pagina_de_livros.campo_quantidade,
        pagina_de_livros.botao_cadastrar,
    ]

    # Act / Assert — cada Tab precisa levar ao próximo elemento, na ordem visual
    for elemento in ordem_esperada:
        page.keyboard.press("Tab")
        expect(elemento).to_be_focused()


def test_pular_para_o_conteudo_leva_direto_ao_formulario(page: Page, url_base):
    # Arrange
    pagina_de_livros = LivrosPage(page, url_base)
    pagina_de_livros.abrir()
    page.keyboard.press("Tab")

    # Act — Enter no link "Pular para o conteúdo" e mais um Tab
    page.keyboard.press("Enter")
    page.keyboard.press("Tab")

    # Assert — o menu foi pulado
    expect(pagina_de_livros.campo_isbn).to_be_focused()


def test_formulario_de_livro_pode_ser_enviado_so_pelo_teclado(page: Page, url_base):
    # Arrange
    livro = LivroFactory.criar_dados()
    pagina_de_livros = LivrosPage(page, url_base)
    pagina_de_livros.abrir()
    pagina_de_livros.campo_isbn.focus()

    # Act — digita e avança com Tab, sem nenhum clique
    page.keyboard.type(livro["isbn"])
    page.keyboard.press("Tab")  # botão de busca
    page.keyboard.press("Tab")
    page.keyboard.type(livro["titulo"])
    page.keyboard.press("Tab")
    page.keyboard.type(livro["autor"])
    page.keyboard.press("Enter")

    # Assert
    expect(pagina_de_livros.linha_do_livro(livro["titulo"])).to_be_visible()
