from playwright.sync_api import Locator, Page


class LeitoresPage:
    def __init__(self, page: Page, url_base: str):
        self.page = page
        self.url_base = url_base
        self.campo_nome = page.get_by_label("Nome", exact=True)
        self.campo_cpf = page.get_by_label("CPF", exact=True)
        self.campo_email = page.get_by_label("E-mail", exact=True)
        self.botao_cadastrar = page.get_by_role("button", name="Cadastrar leitor")

    def abrir(self) -> None:
        self.page.goto(self.url_base + "/leitores")

    def cadastrar(self, nome: str, cpf: str, email: str) -> None:
        self.campo_nome.fill(nome)
        self.campo_cpf.fill(cpf)
        self.campo_email.fill(email)
        self.botao_cadastrar.click()

    def linha_do_leitor(self, nome: str) -> Locator:
        return self.page.get_by_role("row").filter(has_text=nome)
