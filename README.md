# Biblioteca — AT2 de Qualidade e Testes de Software

Sistema de empréstimo de livros (FastAPI + Pydantic + SQLite + páginas HTML)
com testes de integração, E2E com Playwright, auditoria de acessibilidade
WCAG 2.1 AA e teste de carga com Locust.

- Requisitos e regras de negócio: [`PRD.md`](PRD.md)
- Regras de contexto para IA: [`AGENTS.md`](AGENTS.md)
- Transparência no uso de IA: [`AI_USAGE.md`](AI_USAGE.md)

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Instalação

```bash
uv sync                               # cria .venv e instala tudo do uv.lock
uv run playwright install chromium    # navegador dos testes E2E
```

No Linux/WSL, se o Chromium reclamar de bibliotecas faltando (`libnspr4.so`…),
rode uma vez num terminal com senha: `sudo ~/.local/bin/uv run playwright install-deps chromium`.

## Rodando a aplicação

```bash
uv run uvicorn app.main:app --reload
```

- Interface: http://127.0.0.1:8000
- Documentação da API: http://127.0.0.1:8000/docs

O banco `biblioteca.db` é criado na primeira execução. Para usar outro arquivo:
`BIBLIOTECA_DB=outro.db uv run uvicorn app.main:app`.

## Testes

```bash
uv run pytest -v                        # tudo (52 testes)
uv run pytest -v -m integration         # integração (API + páginas, TestClient)
uv run pytest -v -m e2e                 # ponta a ponta no navegador
uv run pytest -v -m accessibility       # Axe WCAG 2.1 AA + teclado
uv run pytest -v -m e2e --headed --slowmo 500   # ver o navegador trabalhando
```

| Suíte | Onde | O que cobre |
|-------|------|-------------|
| Integração | `tests/integracao/` | Regras RN1–RN10, status e payload, padrão AAA, fixture com `yield`, Faker `pt_BR` (`tests/factories.py`), `mocker.patch` na OpenLibrary (sucesso, não encontrado, timeout, erro 500) e na data atual (multa) |
| E2E | `tests/e2e/test_fluxo_emprestimo.py` | Cadastro, erro de ISBN, empréstimo e devolução completos, livro esgotado — via Page Objects (`tests/e2e/pages/`) com `get_by_role`/`get_by_label` |
| Acessibilidade | `tests/e2e/test_acessibilidade.py` | Axe nas 3 páginas e no estado de erro, ordem do `Tab`, link "Pular para o conteúdo", envio de formulário só pelo teclado |

Os testes E2E sobem o app de verdade (uvicorn) numa porta livre com banco
temporário — não precisa deixar o servidor rodando.

## Teste de carga

Com o app rodando em um terminal (`uv run uvicorn app.main:app`), em outro:

```bash
uv run locust --host http://127.0.0.1:8000        # interface em http://localhost:8089
# ou, sem interface, gravando CSV:
uv run locust --headless -u 50 -r 10 -t 60s --host http://127.0.0.1:8000 --csv resultados/carga
```

Cenário (`locustfile.py`): cada usuário virtual cadastra um leitor e um livro
ao entrar e depois, com pausa de 1–3 s entre ações, lista livros (peso 5),
abre a página de empréstimos (3), cadastra livros (2) e empresta + devolve (1).
Um 409 de "sem exemplar disponível" conta como sucesso: é a regra de negócio
funcionando.

### Resultados (2026-11-09, WSL2, 1 processo uvicorn, banco vazio no início)

50 usuários, entrada de 10/s, 60 s — CSVs completos em `resultados/`.

| Métrica | Resultado | Meta (PRD) |
|---------|-----------|------------|
| Requisições | 1 689 | — |
| **RPS** (média) | **28,55** | — |
| Tempo de resposta mediano | 9 ms | — |
| **p95** | **41 ms** | < 500 ms ✅ |
| p99 | 200 ms | — |
| **Taxa de falha** | **0 %** | < 1 % ✅ |

| Endpoint | Reqs | p95 |
|----------|------|-----|
| GET /api/livros | 670 | 17 ms |
| GET /emprestimos (HTML) | 384 | 18 ms |
| POST /api/livros | 309 | 38 ms |
| POST /api/emprestimos | 138 | 38 ms |
| POST /api/emprestimos/[id]/devolucao | 138 | 36 ms |
| POST /api/leitores | 50 | 460 ms |

**Como ler esses números:**

- O RPS é limitado pelo próprio cenário: 50 usuários com pausa de 1–3 s
  geram no máximo ~25–50 req/s. O teste mede **latência sob essa carga**,
  não a capacidade máxima do servidor.
- O p95 alto de `POST /api/leitores` (460 ms) vem do aquecimento: essa rota
  só roda no `on_start`, quando 10 usuários/s entram escrevendo ao mesmo
  tempo num servidor recém-iniciado.
- `GET /api/livros` devolve o acervo inteiro sem paginação; com dezenas de
  milhares de livros essa rota seria o primeiro gargalo.

## Estrutura

```
app/            aplicação (ver AGENTS.md para o papel de cada arquivo)
tests/          factories, integração, e2e (com Page Objects)
locustfile.py   teste de carga
resultados/     CSVs da última execução do Locust
docs/           design e plano de implementação
```
