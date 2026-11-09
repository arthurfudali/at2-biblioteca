from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.isbn import isbn13_valido, normalizar_isbn


class LivroEntrada(BaseModel):
    isbn: str
    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=200)
    quantidade_total: int = Field(ge=1, le=1000)

    @field_validator("isbn")
    @classmethod
    def validar_isbn(cls, valor: str) -> str:
        isbn = normalizar_isbn(valor)
        if not isbn13_valido(isbn):
            raise ValueError("ISBN-13 inválido")
        return isbn


class LivroSaida(BaseModel):
    id: int
    isbn: str
    titulo: str
    autor: str
    quantidade_total: int
    disponiveis: int


class LeitorEntrada(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    cpf: str = Field(pattern=r"^\d{11}$", description="Somente os 11 dígitos")
    email: EmailStr


class LeitorSaida(BaseModel):
    id: int
    nome: str
    cpf: str
    email: str


class EmprestimoEntrada(BaseModel):
    livro_id: int
    leitor_id: int


class EmprestimoSaida(BaseModel):
    id: int
    livro_id: int
    leitor_id: int
    titulo_do_livro: str
    nome_do_leitor: str
    data_emprestimo: date
    data_prevista: date
    data_devolucao: date | None
    multa: float
