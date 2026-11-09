# Design — AT2 QTS: Biblioteca (empréstimo de livros)

## Intenção

Atividade avaliativa AT2 de Qualidade e Testes de Software (Fatec, 2026-2).
Enunciado: https://i-davies.github.io/conteudo-fatec-2026-2/QTS/11_AT2_Testes_de_Integracao_E2E_e_Qualidade_Nao_Funcional/01_Atividade_Avaliativa/

O app é só o pretexto: o que é avaliado são os testes (integração, E2E,
acessibilidade, carga) e a governança de IA. Por isso o domínio é um CRUD
simples com regras de negócio que valem a pena testar. O Arthur vai gravar um
vídeo de até 4 min explicando o projeto, então o código precisa ser fácil de
explicar e de ler (ver estilo em ~/.claude/CLAUDE.md: nomes explícitos, early
return, sem esperteza).

## Objetivos

- Atender todos os itens obrigatórios do enunciado (checklist abaixo).
- `uv run pytest -v` passando 100%, de forma determinística (sem rede real).
- `uv run locust` rodando contra o app local, com números anotados no README.

## Não-objetivos

- Autenticação, usuários, deploy, front-end bonito, framework JS.
- Cobertura de código como meta (foi a AT1).

## Anti-objetivos

- Testes que dependem da internet ou de data/hora real (flaky no vídeo).
- Código "esperto" que o Arthur não consiga explicar na gravação.

## Domínio

**Livro**: id, isbn (único), titulo, autor, quantidade_total.
Disponíveis = quantidade_total − empréstimos ativos daquele livro.

**Leitor**: id, nome, cpf (único), email.

**Empréstimo**: id, livro_id, leitor_id, data_emprestimo, data_prevista
(= data_emprestimo + 14 dias), data_devolucao (nula enquanto ativo), multa.

### Regras de negócio

1. ISBN-13 com dígito verificador válido; ISBN duplicado → 409.
2. Empréstimo só com exemplar disponível; senão → 409.
3. Leitor com 3 empréstimos ativos não pega o 4º → 409.
4. Devolução com atraso: multa = R$ 2,00 × dias de atraso; no prazo = 0.
5. Não excluir livro com empréstimo ativo → 409.
6. Devolver empréstimo já devolvido → 409.

Validação de formato (campos obrigatórios, e-mail, CPF com 11 dígitos) fica
com o Pydantic → 422.

Datas: a data "de hoje" é obtida por uma função própria (`hoje()`) para que
os testes a substituam com `mocker.patch` — assim a regra de multa é testável
sem esperar 14 dias.

### Dependência externa

`POST /livros/preencher/{isbn}` (ou equivalente) consulta a OpenLibrary
(`https://openlibrary.org/isbn/{isbn}.json`, via `httpx`) para sugerir título
e autor. Encapsulada em um módulo `servicos/catalogo_externo.py`. Se a API
falhar (timeout, 404, erro de rede) a rota responde de forma controlada
(ex.: 503 ou 404 com mensagem) e o cadastro manual continua funcionando.
Nos testes ela é sempre mockada: um teste de sucesso e um de falha.

## Arquitetura (decidida)

- Python 3.12, projeto gerenciado com `uv` (`pyproject.toml`).
- FastAPI + Pydantic v2; SQLite via `sqlite3` da biblioteca padrão (sem ORM —
  menos coisa para explicar). Caminho do banco configurável por variável de
  ambiente para os testes usarem um banco temporário.
- Páginas HTML com Jinja2 servidas pelo próprio FastAPI, formulários HTML
  comuns + um pouco de JS puro (fetch) se necessário. HTML semântico com
  `<label for>`, `<main>`, `<h1>`, `lang="pt-BR"` — precisa passar no Axe.
  - `/` → livros: formulário de cadastro + tabela.
  - `/emprestimos` → formulário de empréstimo + lista com botão devolver.
  - Cadastro de leitores pode ser via API e/ou uma terceira página simples.
- API JSON em `/api/...` (CRUD de livros e leitores, emprestar, devolver).

## Testes (checklist do enunciado)

- `tests/factories.py`: Factory com `Faker("pt_BR")` para livro e leitor
  (ISBN válido gerado pela factory).
- `tests/conftest.py`: fixture com `yield` que cria banco temporário,
  entrega `TestClient` e apaga o banco no teardown.
- `tests/integracao/` — `@pytest.mark.integration`, padrão AAA comentado
  (`# Arrange / # Act / # Assert`), verificando status e payload. Uma ou mais
  por regra; `mocker.patch` no catálogo externo (sucesso e falha) e em `hoje()`.
- `tests/e2e/` — `@pytest.mark.e2e`, pytest-playwright, Page Objects em
  `tests/e2e/pages/`, seletores `get_by_role`/`get_by_label`/`get_by_text`.
  O servidor sobe numa fixture de sessão (uvicorn em thread/processo, porta
  livre, banco temporário).
- `tests/e2e/test_acessibilidade.py` — `@pytest.mark.accessibility`, Axe via
  `axe-playwright-python` em cada página sem violações WCAG 2.1 AA, e
  navegação por Tab com `expect(...).to_be_focused()`.
- Marcadores registrados no `pyproject.toml`.
- `locustfile.py`: `HttpUser` com `@task` ponderadas (listar livros mais
  frequente, cadastrar, emprestar/devolver). README com RPS, p95 e taxa de
  falha de uma execução real (ex.: 50 usuários, 1 min).

## Documentos

- `PRD.md`: problema, rotas, páginas, regras, requisitos não funcionais
  avaliados (desempenho, acessibilidade WCAG 2.1 AA — ISO/IEC 25010).
- `AGENTS.md`: regras de contexto para IA (stack, estilo, convenções de teste).
- `AI_USAGE.md`: ferramenta usada (Claude Code), para quê, e como foi auditado.
  Honesto: o código foi gerado com IA e revisado pelo Arthur.
- `README.md`: como instalar e rodar com `uv`, como rodar cada suíte por
  marcador, como rodar o Locust, tabela de resultados de carga.

## Entrega

- Repositório público no GitHub da conta do Arthur — **criar/publicar só
  com confirmação dele**.
- Vídeo é do Arthur; entregar ao final um roteiro de fala de 4 min seguindo
  a ordem obrigatória do enunciado.

## Local

`/home/arthur/fatec/QTS/at2-biblioteca/`

## Decisões do Claude (revisar)

- Git local com um commit por etapa (histórico ajuda o AI_USAGE.md mostrar
  auditoria); criar repositório no GitHub e dar push só com confirmação.
- OpenLibrary devolve autor como chave (`/authors/OL..A`): uma segunda
  chamada busca o nome; as duas ficam dentro do módulo mockado.
- A rota de preenchimento externo fica fora do E2E (servidor em outro
  processo, não dá para mockar) — coberta só na integração.
- Livro com empréstimos apenas devolvidos pode ser excluído.
- No Locust, 409 de regra de negócio não conta como falha
  (`catch_response`); ISBNs gerados únicos por usuário virtual.

## Fica a critério do construtor

Nomes de rotas exatas, layout das páginas, estrutura interna de módulos,
quantidade de testes além do mínimo por regra, parâmetros do Locust.
