# AGENTS.md — regras de contexto para assistentes de IA

Este arquivo é lido por agentes de IA (Claude Code, Cursor, Copilot etc.)
antes de mexer no projeto. Ele define o que o agente pode assumir e o que
precisa respeitar.

## Projeto

Sistema de empréstimo de livros (FastAPI + SQLite + Jinja2). Requisitos e
regras de negócio em `PRD.md` — **o PRD é a fonte da verdade**; se o código
divergir dele, o código está errado ou o PRD precisa ser atualizado antes.

## Stack (não trocar sem pedir)

- Python 3.12, dependências gerenciadas **só com `uv`** (`uv add`, `uv run`). Nunca `pip install`.
- FastAPI + Pydantic v2 para API e validação.
- SQLite pela biblioteca padrão `sqlite3`, **sem ORM**. Todo SQL fica em `app/repositorio.py`.
- Páginas Jinja2 em `app/templates/`, sem framework JS.
- `httpx` para chamadas externas.

## Estrutura

```
app/
  main.py              # cria o app e registra rotas
  db.py                # conexão e esquema; use o tipo Conexao nas rotas
  repositorio.py       # todo o SQL
  regras.py            # constantes e cálculos puros (prazo, multa, limite)
  datas.py             # hoje() — sempre use esta função, nunca date.today() direto
  servicos/biblioteca.py        # operações com regra de negócio (sem HTTP)
  servicos/catalogo_externo.py  # OpenLibrary
  rotas/               # API (/api/...) e páginas HTML
tests/
  factories.py         # Faker("pt_BR")
  integracao/          # @pytest.mark.integration
  e2e/                 # @pytest.mark.e2e e @pytest.mark.accessibility
    pages/             # Page Objects
```

## Estilo de código

- Nomes explícitos em português, mesmo que longos (`emprestimos_ativos_do_leitor`, não `n`).
- Early return em vez de `if` aninhado; no máximo ~2 níveis de indentação.
- Uma função faz uma coisa. Sem one-liners espertos, ternários aninhados ou `reduce`.
- Comentário explica o **porquê**, nunca o quê.
- Regras de negócio levantam `NaoEncontrado` / `RegraViolada`; só as rotas traduzem para HTTP.

## Testes (obrigatório para qualquer mudança)

- Escreva o teste antes do código e veja ele falhar.
- Integração: `TestClient` via fixture `cliente` (banco temporário por teste), padrão
  **AAA** com comentários `# Arrange / # Act / # Assert`, conferindo **status e payload**.
- Dados de teste **sempre** pelas factories de `tests/factories.py`, nunca dados fixos
  copiados entre testes (exceto valores que o próprio teste precisa controlar, como um ISBN inválido).
- **Nunca** acessar a rede real em teste: mocke `buscar_dados_do_livro` ou `httpx.get`
  com `mocker.patch`, cobrindo sucesso **e** falha.
- **Nunca** depender da data real: mocke `app.servicos.biblioteca.hoje`.
- E2E: só pelo Page Object; seletores semânticos (`get_by_role`, `get_by_label`,
  `get_by_text`). Proibido seletor CSS/XPath.
- Toda página nova precisa entrar no teste parametrizado do Axe e passar com zero violações WCAG 2.1 AA.
- Antes de dizer que terminou: `uv run pytest -v` com tudo passando.

## Proibido

- Credenciais, tokens ou dados pessoais reais no código ou nos testes.
- Desativar ou pular teste para "fazer passar".
- Concatenar valores em SQL — use sempre parâmetros `?`.
