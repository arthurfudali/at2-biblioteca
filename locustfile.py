"""Teste de carga da Biblioteca.

Uso (com o app rodando em outro terminal):
    uv run locust --host http://127.0.0.1:8000
    -> abrir http://localhost:8089, escolher usuários e taxa de entrada

Sem interface:
    uv run locust --headless -u 50 -r 10 -t 60s --host http://127.0.0.1:8000 --csv resultados/carga
"""

import random

from faker import Faker
from locust import HttpUser, between, task
from locust.exception import StopUser

fake = Faker("pt_BR")


def gerar_isbn_valido() -> str:
    # unique: dois usuários virtuais nunca tentam cadastrar o mesmo ISBN.
    return fake.unique.isbn13(separator="")


class UsuarioDaBiblioteca(HttpUser):
    # Cada usuário virtual espera de 1 a 3 s entre uma ação e outra,
    # imitando uma pessoa usando o sistema.
    wait_time = between(1, 3)

    def on_start(self):
        """Cada usuário virtual começa com um leitor e um livro próprios."""
        leitor = {"nome": fake.name(), "cpf": fake.unique.cpf().replace(".", "").replace("-", ""),
                  "email": fake.unique.email()}
        resposta = self.client.post("/api/leitores", json=leitor)
        if resposta.status_code != 201:
            # Sem leitor o usuário virtual não tem o que fazer; para só ele,
            # em vez de espalhar exceções pelo relatório.
            raise StopUser()
        self.leitor_id = resposta.json()["id"]

        self.ids_dos_meus_livros = []
        self.cadastrar_livro()
        if not self.ids_dos_meus_livros:
            raise StopUser()

    # O peso (5, 3, 2, 1) define a proporção: listar acontece 5x mais que emprestar.
    @task(5)
    def listar_livros(self):
        self.client.get("/api/livros")

    @task(3)
    def abrir_pagina_de_emprestimos(self):
        self.client.get("/emprestimos")

    @task(2)
    def cadastrar_livro(self):
        livro = {
            "isbn": gerar_isbn_valido(),
            "titulo": fake.sentence(nb_words=3).rstrip("."),
            "autor": fake.name(),
            "quantidade_total": random.randint(1, 3),
        }
        resposta = self.client.post("/api/livros", json=livro)
        if resposta.status_code == 201:
            self.ids_dos_meus_livros.append(resposta.json()["id"])

    @task(1)
    def emprestar_e_devolver(self):
        livro_id = random.choice(self.ids_dos_meus_livros)
        pedido = {"livro_id": livro_id, "leitor_id": self.leitor_id}

        # catch_response permite decidir o que é falha. Um 409 ("sem exemplar
        # disponível") é a regra de negócio funcionando, não um erro do sistema.
        with self.client.post("/api/emprestimos", json=pedido, catch_response=True) as resposta:
            if resposta.status_code == 409:
                resposta.success()
                return
            if resposta.status_code != 201:
                resposta.failure(f"Status inesperado: {resposta.status_code}")
                return
            emprestimo_id = resposta.json()["id"]

        # name= agrupa todas as devoluções numa linha só do relatório,
        # em vez de uma linha por id.
        self.client.post(
            f"/api/emprestimos/{emprestimo_id}/devolucao",
            name="/api/emprestimos/[id]/devolucao",
        )
