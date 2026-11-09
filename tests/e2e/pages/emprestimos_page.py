from playwright.sync_api import Locator, Page


class EmprestimosPage:
    def __init__(self, page: Page, url_base: str):
        self.page = page
        self.url_base = url_base
        self.seletor_livro = page.get_by_label("Livro", exact=True)
        self.seletor_leitor = page.get_by_label("Leitor", exact=True)
        self.botao_emprestar = page.get_by_role("button", name="Emprestar")
        self.mensagem_de_erro = page.get_by_role("alert")
        self.aviso = page.get_by_role("status")

    def abrir(self) -> None:
        self.page.goto(self.url_base + "/emprestimos")

    def emprestar(self, titulo: str, nome_do_leitor: str) -> None:
        self.seletor_livro.select_option(label=titulo)
        self.seletor_leitor.select_option(label=nome_do_leitor)
        self.botao_emprestar.click()

    def linha_do_emprestimo(self, titulo: str) -> Locator:
        return self.page.get_by_role("row").filter(has_text=titulo)

    def devolver(self, titulo: str, nome_do_leitor: str) -> None:
        nome_do_botao = f"Devolver {titulo} de {nome_do_leitor}"
        self.page.get_by_role("button", name=nome_do_botao).click()
