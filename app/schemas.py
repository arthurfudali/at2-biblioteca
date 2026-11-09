from pydantic import BaseModel, Field, field_validator

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
