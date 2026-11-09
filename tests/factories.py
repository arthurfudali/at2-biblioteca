"""Factories de dados sintéticos com Faker em português.

Cada factory devolve um dicionário pronto para mandar no corpo de um POST.
Qualquer campo pode ser sobrescrito para montar um cenário específico,
ex.: LivroFactory.criar_dados(quantidade_total=1).
"""

from faker import Faker

fake = Faker("pt_BR")


class LivroFactory:
    @staticmethod
    def criar_dados(**sobrescritas) -> dict:
        # unique evita que dois livros do mesmo teste caiam no mesmo ISBN
        # e disparem a regra de duplicidade sem querer.
        dados = {
            "isbn": fake.unique.isbn13(separator=""),
            "titulo": fake.sentence(nb_words=3).rstrip("."),
            "autor": fake.name(),
            "quantidade_total": fake.random_int(min=1, max=5),
        }
        dados.update(sobrescritas)
        return dados


class LeitorFactory:
    @staticmethod
    def criar_dados(**sobrescritas) -> dict:
        dados = {
            "nome": fake.name(),
            "cpf": fake.unique.cpf().replace(".", "").replace("-", ""),
            "email": fake.unique.email(),
        }
        dados.update(sobrescritas)
        return dados
