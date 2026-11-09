import os
import sqlite3

ESQUEMA = """
CREATE TABLE IF NOT EXISTS livros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    autor TEXT NOT NULL,
    quantidade_total INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS leitores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS emprestimos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    livro_id INTEGER NOT NULL REFERENCES livros(id),
    leitor_id INTEGER NOT NULL REFERENCES leitores(id),
    data_emprestimo TEXT NOT NULL,
    data_prevista TEXT NOT NULL,
    data_devolucao TEXT,
    multa REAL NOT NULL DEFAULT 0
);
"""


def caminho_do_banco() -> str:
    # Lido a cada chamada (e não uma vez no import) para que os testes
    # possam apontar cada execução para um banco temporário diferente.
    return os.environ.get("BIBLIOTECA_DB", "biblioteca.db")


def conectar() -> sqlite3.Connection:
    # timeout=10: sob carga (Locust), várias requisições escrevem ao mesmo
    # tempo; em vez de falhar na hora com "database is locked", a conexão
    # espera até 10 s pela vez dela.
    conexao = sqlite3.connect(caminho_do_banco(), timeout=10)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas() -> None:
    conexao = conectar()
    # WAL deixa leituras acontecerem enquanto outra conexão escreve.
    # É uma configuração do arquivo, então basta ligar uma vez.
    conexao.execute("PRAGMA journal_mode = WAL")
    conexao.executescript(ESQUEMA)
    conexao.close()


def obter_conexao():
    """Dependência do FastAPI: abre uma conexão por requisição e sempre fecha."""
    conexao = conectar()
    try:
        yield conexao
        conexao.commit()
    finally:
        conexao.close()
