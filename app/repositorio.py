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


def listar_leitores(conexao: sqlite3.Connection) -> list[dict]:
    linhas = conexao.execute("SELECT * FROM leitores ORDER BY nome").fetchall()
    return [dict(linha) for linha in linhas]


def buscar_leitor(conexao: sqlite3.Connection, leitor_id: int) -> dict | None:
    linha = conexao.execute("SELECT * FROM leitores WHERE id = ?", (leitor_id,)).fetchone()
    if linha is None:
        return None
    return dict(linha)


def inserir_leitor(conexao: sqlite3.Connection, dados: dict) -> int:
    try:
        cursor = conexao.execute(
            "INSERT INTO leitores (nome, cpf, email) VALUES (?, ?, ?)",
            (dados["nome"], dados["cpf"], dados["email"]),
        )
    except sqlite3.IntegrityError as erro:
        raise RegistroDuplicado from erro
    return cursor.lastrowid


SELECT_EMPRESTIMO = """
SELECT
    emprestimos.*,
    livros.titulo AS titulo_do_livro,
    leitores.nome AS nome_do_leitor
FROM emprestimos
JOIN livros ON livros.id = emprestimos.livro_id
JOIN leitores ON leitores.id = emprestimos.leitor_id
"""


def listar_emprestimos(conexao: sqlite3.Connection, somente_ativos: bool) -> list[dict]:
    consulta = SELECT_EMPRESTIMO
    if somente_ativos:
        consulta += " WHERE emprestimos.data_devolucao IS NULL"
    consulta += " ORDER BY emprestimos.id DESC"
    linhas = conexao.execute(consulta).fetchall()
    return [dict(linha) for linha in linhas]


def buscar_emprestimo(conexao: sqlite3.Connection, emprestimo_id: int) -> dict | None:
    linha = conexao.execute(
        SELECT_EMPRESTIMO + " WHERE emprestimos.id = ?", (emprestimo_id,)
    ).fetchone()
    if linha is None:
        return None
    return dict(linha)


def contar_emprestimos_ativos_do_leitor(conexao: sqlite3.Connection, leitor_id: int) -> int:
    linha = conexao.execute(
        "SELECT COUNT(*) FROM emprestimos WHERE leitor_id = ? AND data_devolucao IS NULL",
        (leitor_id,),
    ).fetchone()
    return linha[0]


def contar_emprestimos_ativos_do_livro(conexao: sqlite3.Connection, livro_id: int) -> int:
    linha = conexao.execute(
        "SELECT COUNT(*) FROM emprestimos WHERE livro_id = ? AND data_devolucao IS NULL",
        (livro_id,),
    ).fetchone()
    return linha[0]


def inserir_emprestimo(
    conexao: sqlite3.Connection, livro_id: int, leitor_id: int, data_emprestimo, data_prevista
) -> int:
    cursor = conexao.execute(
        "INSERT INTO emprestimos (livro_id, leitor_id, data_emprestimo, data_prevista)"
        " VALUES (?, ?, ?, ?)",
        (livro_id, leitor_id, data_emprestimo.isoformat(), data_prevista.isoformat()),
    )
    return cursor.lastrowid


def registrar_devolucao(
    conexao: sqlite3.Connection, emprestimo_id: int, data_devolucao, multa: float
) -> None:
    conexao.execute(
        "UPDATE emprestimos SET data_devolucao = ?, multa = ? WHERE id = ?",
        (data_devolucao.isoformat(), multa, emprestimo_id),
    )
