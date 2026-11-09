from playwright.sync_api import Locator, Page


class LivrosPage:
    """Page Object da página de livros: os testes falam em "cadastrar livro",
    não em qual campo preencher. Se o HTML mudar, só esta classe muda."""

    def __init__(self, page: Page, url_base: str):
        self.page = page
        self.url_base = url_base
        self.campo_isbn = page.get_by_label("ISBN", exact=True)
        self.campo_titulo = page.get_by_label("Título", exact=True)
        self.campo_autor = page.get_by_label("Autor", exact=True)
        self.campo_quantidade = page.get_by_label("Quantidade", exact=True)
        self.botao_buscar_isbn = page.get_by_role("button", name="Buscar dados pelo ISBN")
        self.botao_cadastrar = page.get_by_role("button", name="Cadastrar livro")
        self.mensagem_de_erro = page.get_by_role("alert")

    def abrir(self) -> None:
        self.page.goto(self.url_base + "/")

    def cadastrar(self, isbn: str, titulo: str, autor: str, quantidade: int) -> None:
        self.campo_isbn.fill(isbn)
        self.campo_titulo.fill(titulo)
        self.campo_autor.fill(autor)
        self.campo_quantidade.fill(str(quantidade))
        self.botao_cadastrar.click()

    def linha_do_livro(self, titulo: str) -> Locator:
        return self.page.get_by_role("row").filter(has_text=titulo)

    def excluir(self, titulo: str) -> None:
        self.page.get_by_role("button", name=f"Excluir {titulo}").click()
