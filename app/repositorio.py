"""Todo o SQL do sistema. As rotas da API e as páginas HTML usam estas funções."""

import sqlite3

# "disponiveis" não é guardado no banco: é calculado na hora a partir dos
# empréstimos ativos, assim nunca fica dessincronizado.
SELECT_LIVRO = """
SELECT
    livros.*,
    livros.quantidade_total - (
        SELECT COUNT(*) FROM emprestimos
        WHERE emprestimos.livro_id = livros.id AND emprestimos.data_devolucao IS NULL
    ) AS disponiveis
FROM livros
"""


class RegistroDuplicado(Exception):
    """Violação de UNIQUE no banco (ISBN ou CPF repetido)."""


def listar_livros(conexao: sqlite3.Connection) -> list[dict]:
    linhas = conexao.execute(SELECT_LIVRO + " ORDER BY livros.titulo").fetchall()
    return [dict(linha) for linha in linhas]


def buscar_livro(conexao: sqlite3.Connection, livro_id: int) -> dict | None:
    linha = conexao.execute(SELECT_LIVRO + " WHERE livros.id = ?", (livro_id,)).fetchone()
    if linha is None:
        return None
    return dict(linha)


def inserir_livro(conexao: sqlite3.Connection, dados: dict) -> int:
    try:
        cursor = conexao.execute(
            "INSERT INTO livros (isbn, titulo, autor, quantidade_total) VALUES (?, ?, ?, ?)",
            (dados["isbn"], dados["titulo"], dados["autor"], dados["quantidade_total"]),
        )
    except sqlite3.IntegrityError as erro:
        raise RegistroDuplicado from erro
    return cursor.lastrowid


def atualizar_livro(conexao: sqlite3.Connection, livro_id: int, dados: dict) -> None:
    try:
        conexao.execute(
            "UPDATE livros SET isbn = ?, titulo = ?, autor = ?, quantidade_total = ? WHERE id = ?",
            (dados["isbn"], dados["titulo"], dados["autor"], dados["quantidade_total"], livro_id),
        )
    except sqlite3.IntegrityError as erro:
        raise RegistroDuplicado from erro


def excluir_livro(conexao: sqlite3.Connection, livro_id: int) -> None:
    conexao.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
