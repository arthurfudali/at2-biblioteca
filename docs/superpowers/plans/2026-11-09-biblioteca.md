# Biblioteca (AT2 QTS) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** App FastAPI de empréstimo de livros com suítes de integração, E2E, acessibilidade e carga que atendem a AT2.

**Architecture:** Pacote `app/` com FastAPI + Pydantic, SQLite puro (`sqlite3`), páginas Jinja2. A data atual e o catálogo externo ficam em funções próprias para serem mockadas. Testes em `tests/` separados por marcador.

**Tech Stack:** Python 3.12, uv, FastAPI, Pydantic v2, Jinja2, httpx, uvicorn, pytest, pytest-mock, Faker, pytest-playwright, axe-playwright-python, Locust.

**Spec:** `docs/superpowers/specs/2026-11-09-biblioteca-design.md`

## Global Constraints

- Ambiente: WSL, Python 3.12 (`/usr/bin/python3.12`), `uv` instalado em `~/.local/bin`.
- Raiz: `/home/arthur/fatec/QTS/at2-biblioteca/`.
- Estilo do Arthur: nomes explícitos em português, early return, máx. ~2 níveis de indentação, comentário só de "porquê", nada de one-liner esperto.
- Testes nunca acessam a rede real nem dependem da data real.
- Marcadores: `integration`, `e2e`, `accessibility` registrados no `pyproject.toml`.
- Integração usa AAA comentado (`# Arrange`, `# Act`, `# Assert`) e confere status + payload.
- Erros de negócio → 409 com `{"detail": "<mensagem em pt-BR>"}`; não encontrado → 404; formato inválido → 422 (Pydantic).
- Prazo de empréstimo 14 dias; multa R$ 2,00/dia de atraso; limite 3 empréstimos ativos por leitor.
- Git local com commit por task; nada de `gh repo create`/push sem confirmação do Arthur.

## Review Focus

1. ISBN digitado com hífens/espaços (`978-85-...`) → normalizado e aceito se o dígito confere. Teste na Task 1.
2. Emprestar para livro ou leitor inexistente → 404, não 500. Teste na Task 3.
3. CPF de leitor duplicado → 409. Teste na Task 2.
4. Reduzir `quantidade_total` abaixo dos empréstimos ativos via PUT → 409. Teste na Task 3.
5. SQLite sob carga concorrente ("database is locked") → conexão por requisição com `timeout=10` e WAL; verificado pela taxa de falha do Locust na Task 7.

---

### Task 1: Scaffold + CRUD de livros com validação de ISBN

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `app/__init__.py`, `app/main.py`, `app/db.py`, `app/isbn.py`, `app/schemas.py`, `app/rotas/__init__.py`, `app/rotas/livros.py`
- Test: `tests/conftest.py`, `tests/factories.py`, `tests/integracao/test_livros.py`

**Interfaces:**
- Produces:
  - `app.db.caminho_do_banco() -> str` (lê env `BIBLIOTECA_DB`, padrão `biblioteca.db`)
  - `app.db.conectar() -> sqlite3.Connection` (`row_factory=sqlite3.Row`, `timeout=10`, `PRAGMA foreign_keys=ON`, WAL)
  - `app.db.criar_tabelas() -> None` (livros, leitores, emprestimos; chamado no startup/lifespan)
  - `app.isbn.normalizar_isbn(texto: str) -> str` (remove hífens/espaços)
  - `app.isbn.isbn13_valido(isbn: str) -> bool`
  - `app.main.app: FastAPI`
  - Schemas: `LivroEntrada(isbn, titulo, autor, quantidade_total: int >= 1)`, `LivroSaida(+ id, disponiveis)`
  - Rotas: `GET/POST /api/livros`, `GET/PUT/DELETE /api/livros/{id}`
  - `tests.factories.LivroFactory.criar_dados(**sobrescritas) -> dict` com ISBN-13 válido gerado; `LeitorFactory.criar_dados(**sobrescritas) -> dict` (nome, cpf 11 dígitos sem máscara, email) — Faker("pt_BR")
  - Fixture `cliente` (function scope): `tmp_path` → seta `BIBLIOTECA_DB` com `monkeypatch`, `yield TestClient(app)` dentro de `with`, teardown apaga o arquivo.

- [ ] **Step 1:** Instalar uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`), `git init`, `uv init --app --python 3.12`, `uv add fastapi uvicorn jinja2 httpx python-multipart`, `uv add --dev pytest pytest-mock faker pytest-playwright axe-playwright-python locust`. Registrar marcadores em `[tool.pytest.ini_options]`.
- [ ] **Step 2: Testes que falham** em `tests/integracao/test_livros.py` (todos `@pytest.mark.integration`):
  - `test_cadastrar_livro_valido_retorna_201` — status 201, payload ecoa titulo/isbn, `disponiveis == quantidade_total`
  - `test_cadastrar_livro_com_isbn_invalido_retorna_422` — isbn `9788535902779` (dígito errado) → 422
  - `test_cadastrar_isbn_com_hifens_e_normalizado` — `978-85-359-0277-8` → 201, payload `isbn == "9788535902778"`
  - `test_cadastrar_isbn_duplicado_retorna_409`
  - `test_listar_livros_retorna_cadastrados`
  - `test_buscar_livro_inexistente_retorna_404`
  - `test_atualizar_livro_altera_titulo`
  - `test_excluir_livro_sem_emprestimo_retorna_204`
- [ ] **Step 3:** Rodar `uv run pytest -m integration -v` → FAIL (import error).
- [ ] **Step 4:** Implementar. Validação do ISBN num `field_validator` do Pydantic (normaliza, depois valida → 422). Duplicidade capturando `sqlite3.IntegrityError` → 409.
- [ ] **Step 5:** `uv run pytest -m integration -v` → 8 passed.
- [ ] **Step 6:** Commit `feat: CRUD de livros com validação de ISBN`.

### Task 2: Leitores

**Files:** Create `app/rotas/leitores.py`; Modify `app/schemas.py`, `app/main.py`; Test `tests/integracao/test_leitores.py`

**Interfaces:**
- Produces: `LeitorEntrada(nome: str min 3, cpf: str pattern ^\d{11}$, email: EmailStr)` (adicionar `email-validator`), `LeitorSaida(+ id)`; rotas `GET/POST /api/leitores`, `GET /api/leitores/{id}`.

- [ ] **Step 1: Testes** (`@pytest.mark.integration`): `test_cadastrar_leitor_valido_retorna_201`, `test_cadastrar_leitor_email_invalido_retorna_422`, `test_cadastrar_leitor_cpf_duplicado_retorna_409`, `test_listar_leitores`.
- [ ] **Step 2:** Rodar → FAIL. **Step 3:** Implementar. **Step 4:** Rodar → PASS.
- [ ] **Step 5:** Commit `feat: cadastro de leitores`.

### Task 3: Empréstimos e regras de negócio

**Files:** Create `app/datas.py`, `app/regras.py`, `app/rotas/emprestimos.py`; Modify `app/rotas/livros.py` (DELETE/PUT), `app/schemas.py`; Test `tests/integracao/test_emprestimos.py`

**Interfaces:**
- Produces:
  - `app.datas.hoje() -> date` (wrapper de `date.today()`; os testes fazem `mocker.patch("app.rotas.emprestimos.hoje", ...)` — importar como `from app.datas import hoje` no módulo de rotas, por isso o patch é no módulo que usa)
  - `app.regras.PRAZO_EMPRESTIMO_DIAS = 14`, `MULTA_POR_DIA = 2.0`, `LIMITE_EMPRESTIMOS_ATIVOS = 3`
  - `app.regras.calcular_multa(data_prevista: date, data_devolucao: date) -> float`
  - `EmprestimoEntrada(livro_id: int, leitor_id: int)`, `EmprestimoSaida(id, livro_id, leitor_id, data_emprestimo, data_prevista, data_devolucao: date|None, multa: float)`
  - Rotas: `GET /api/emprestimos` (com `?ativos=true` opcional), `POST /api/emprestimos` → 201, `POST /api/emprestimos/{id}/devolucao` → 200
  - Fixtures novas em conftest: `livro_cadastrado`, `leitor_cadastrado` (dicts do payload de resposta).

- [ ] **Step 1: Testes** (`@pytest.mark.integration`):
  - `test_emprestar_livro_disponivel_retorna_201` — `data_prevista == data_emprestimo + 14 dias`, livro passa a ter `disponiveis` reduzido
  - `test_emprestar_sem_exemplar_disponivel_retorna_409` (livro com quantidade 1, dois empréstimos)
  - `test_leitor_com_tres_emprestimos_nao_pega_quarto` → 409
  - `test_emprestar_livro_inexistente_retorna_404` e `test_emprestar_para_leitor_inexistente_retorna_404`
  - `test_devolucao_no_prazo_multa_zero` — patch `hoje` para data dentro do prazo, `multa == 0`
  - `test_devolucao_com_5_dias_de_atraso_multa_10_reais` — patch `hoje` em 2026-11-01 no empréstimo e 2026-11-20 na devolução → `multa == 10.0`
  - `test_devolver_duas_vezes_retorna_409`
  - `test_excluir_livro_com_emprestimo_ativo_retorna_409`
  - `test_excluir_livro_com_emprestimos_devolvidos_retorna_204`
  - `test_reduzir_quantidade_abaixo_dos_ativos_retorna_409`
- [ ] **Step 2:** Rodar → FAIL. **Step 3:** Implementar (checagens com early return na ordem: existe livro → existe leitor → limite do leitor → disponibilidade). **Step 4:** Rodar → PASS.
- [ ] **Step 5:** Commit `feat: empréstimos, devolução e multa`.

### Task 4: Catálogo externo (OpenLibrary) com mocks

**Files:** Create `app/servicos/__init__.py`, `app/servicos/catalogo_externo.py`; Modify `app/rotas/livros.py`; Test `tests/integracao/test_catalogo_externo.py`

**Interfaces:**
- Produces:
  - `class CatalogoIndisponivel(Exception)`
  - `buscar_dados_do_livro(isbn: str) -> dict | None` — `{"titulo", "autor"}`; `None` se 404; levanta `CatalogoIndisponivel` em timeout/erro de rede/5xx. Usa `httpx.get(..., timeout=5)` em `https://openlibrary.org/isbn/{isbn}.json` e depois `https://openlibrary.org{authors[0].key}.json` para o nome.
  - Rota `GET /api/livros/preencher/{isbn}` → 200 `{"titulo","autor"}`; 404 `"ISBN não encontrado no catálogo"`; 503 `"Catálogo externo indisponível, preencha manualmente"`.

- [ ] **Step 1: Testes** (`@pytest.mark.integration`, `mocker.patch("app.rotas.livros.buscar_dados_do_livro", ...)`):
  - `test_preencher_isbn_sucesso_retorna_dados_do_catalogo` (return_value dict)
  - `test_preencher_isbn_nao_encontrado_retorna_404` (return_value None)
  - `test_preencher_catalogo_fora_do_ar_retorna_503` (side_effect `CatalogoIndisponivel`)
  - `test_buscar_dados_converte_resposta_da_openlibrary` — patch `httpx.get` no módulo do serviço com dois `Mock` de resposta; confere `{"titulo": ..., "autor": ...}`
  - `test_buscar_dados_timeout_vira_catalogo_indisponivel` — `side_effect=httpx.TimeoutException("x")`
- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5:** Commit `feat: preenchimento por ISBN via OpenLibrary`.

### Task 5: Páginas HTML

**Files:** Create `app/rotas/paginas.py`, `app/templates/base.html`, `app/templates/livros.html`, `app/templates/emprestimos.html`, `app/templates/leitores.html`, `app/static/estilo.css`; Test `tests/integracao/test_paginas.py`

**Interfaces:**
- Produces páginas (formulários HTML com POST tradicional + redirect 303; mensagens de erro renderizadas na página num `<p role="alert">`):
  - `GET /` livros: `<h1>Livros</h1>`, form com labels "ISBN", "Título", "Autor", "Quantidade", botão "Cadastrar livro"; tabela com cabeçalhos; botão "Excluir" por linha.
  - `GET /leitores`: labels "Nome", "CPF", "E-mail", botão "Cadastrar leitor".
  - `GET /emprestimos`: `<select>` com labels "Livro" e "Leitor", botão "Emprestar"; tabela de ativos com botão "Devolver"; multa exibida após devolução.
  - `base.html`: `lang="pt-BR"`, `<title>`, `<nav aria-label="Principal">` com links Livros/Leitores/Empréstimos, `<main>`, contraste AA.
  - Lógica das páginas reaproveita funções do repositório/rotas da API (sem duplicar SQL): extrair consultas para `app/repositorio.py` se ainda estiverem nas rotas.

- [ ] **Step 1: Testes** (`@pytest.mark.integration`): `test_pagina_livros_retorna_html`, `test_pagina_emprestimos_lista_ativos`.
- [ ] **Step 2–4:** FAIL → implementar → PASS; rodar suíte inteira de integração.
- [ ] **Step 5:** Commit `feat: interface web`.

### Task 6: E2E com Playwright (POM) e acessibilidade

**Files:** Create `tests/e2e/conftest.py`, `tests/e2e/pages/livros_page.py`, `tests/e2e/pages/leitores_page.py`, `tests/e2e/pages/emprestimos_page.py`, `tests/e2e/test_fluxo_emprestimo.py`, `tests/e2e/test_acessibilidade.py`

**Interfaces:**
- Consumes: páginas da Task 5.
- Produces:
  - Fixture de sessão `url_base` — sobe `uvicorn app.main:app` em `subprocess.Popen` numa porta livre com `BIBLIOTECA_DB` em diretório temporário, espera responder, `yield f"http://127.0.0.1:{porta}"`, encerra no teardown.
  - Page Objects: `LivrosPage(page, url_base)` com `abrir()`, `cadastrar(isbn, titulo, autor, quantidade)`, `linha_do_livro(titulo) -> Locator`; `LeitoresPage.cadastrar(nome, cpf, email)`; `EmprestimosPage.emprestar(titulo, nome_leitor)`, `devolver(titulo)`, `mensagem_de_erro() -> Locator`. Só `get_by_role`/`get_by_label`/`get_by_text`.

- [ ] **Step 1:** `uv run playwright install chromium` (se pedir deps do sistema: Arthur roda `! sudo uv run playwright install-deps chromium`).
- [ ] **Step 2: Testes E2E** (`@pytest.mark.e2e`), dados com as factories:
  - `test_cadastrar_livro_aparece_na_tabela`
  - `test_fluxo_completo_emprestar_e_devolver`
  - `test_emprestar_livro_esgotado_mostra_erro`
- [ ] **Step 3: Testes de acessibilidade** (`@pytest.mark.accessibility`):
  - `test_pagina_sem_violacoes_wcag_aa` parametrizado em `/`, `/leitores`, `/emprestimos` — `Axe().run(page, options={"runOnly": {"type": "tag", "values": ["wcag2a","wcag2aa","wcag21a","wcag21aa"]}})`, `assert resultado.violations_count == 0, resultado.generate_report()`
  - `test_navegacao_por_tab_no_formulario_de_livro` — Tab a partir do início segue: link de navegação(s) → ISBN → Título → Autor → Quantidade → botão; `expect(...).to_be_focused()` em cada.
- [ ] **Step 4:** `uv run pytest -m "e2e or accessibility" -v` → PASS (corrigir HTML até o Axe zerar).
- [ ] **Step 5:** `uv run pytest -v` completo → tudo PASS. Commit `test: E2E e acessibilidade`.

### Task 7: Carga com Locust

**Files:** Create `locustfile.py`; Modify `README.md`

**Interfaces:**
- `class UsuarioBiblioteca(HttpUser)`, `wait_time = between(1, 3)`, `on_start` cadastra um leitor (CPF/ISBN únicos via Faker + contador).
- `@task(5) listar_livros`, `@task(2) cadastrar_livro`, `@task(1) emprestar_e_devolver` — 409 marcado `response.success()` via `catch_response=True`.

- [ ] **Step 1:** Escrever locustfile; subir app (`uv run uvicorn app.main:app`) com banco limpo.
- [ ] **Step 2:** `uv run locust --headless -u 50 -r 10 -t 60s --host http://127.0.0.1:8000 --csv resultados/carga` → falhas 0%.
- [ ] **Step 3:** Anotar RPS, p95 e taxa de falha (do `carga_stats.csv`, linha Aggregated) no README.
- [ ] **Step 4:** Commit `test: teste de carga com Locust`.

### Task 8: Documentação e governança de IA

**Files:** Create `PRD.md`, `AGENTS.md`, `AI_USAGE.md`, `ROTEIRO_VIDEO.md`; Modify `README.md`

- [ ] **Step 1:** `PRD.md` — problema, personas (bibliotecário), rotas da API e páginas, regras 1–6, RNFs avaliados (Desempenho: p95 < 500 ms com 50 usuários, falhas < 1%; Acessibilidade: WCAG 2.1 AA sem violações no Axe, operável por teclado — ISO/IEC 25010).
- [ ] **Step 2:** `AGENTS.md` — stack, estrutura, estilo do código, convenções de teste (marcadores, AAA, factories, mocks, POM, seletores semânticos), proibições (rede real em teste).
- [ ] **Step 3:** `AI_USAGE.md` — ferramenta (Claude Code / Claude Opus), onde foi usada, como foi auditado (revisão do código, execução das suítes, correções feitas), deixando campos para o Arthur completar com a revisão pessoal dele.
- [ ] **Step 4:** `README.md` — instalação do uv, `uv sync`, `uv run playwright install chromium`, rodar app, `uv run pytest -v`, por marcador, Locust (com e sem UI), tabela de carga.
- [ ] **Step 5:** `ROTEIRO_VIDEO.md` — fala de ~4 min seguindo a ordem obrigatória com tempos e arquivos a mostrar.
- [ ] **Step 6:** `uv run pytest -v` final → tudo PASS. Commit `docs: PRD, governança de IA, README e roteiro`.
