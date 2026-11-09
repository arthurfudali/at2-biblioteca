# PRD — Biblioteca: sistema de empréstimo de livros

## 1. Problema

Uma biblioteca pequena controla acervo e empréstimos em planilha. Não há
controle de quantos exemplares estão na rua, quem está com quais livros nem
cálculo de multa por atraso. O sistema substitui a planilha por uma aplicação
web simples, operada pelo bibliotecário no balcão.

**Usuário:** bibliotecário (único perfil, sem autenticação nesta versão).

## 2. Escopo

- Cadastro, consulta, edição e exclusão de livros.
- Cadastro e consulta de leitores.
- Empréstimo e devolução com cálculo de multa.
- Sugestão de título e autor pelo ISBN, consultando a OpenLibrary.

**Fora do escopo:** login, reservas, renovação, pagamento da multa, relatórios.

## 3. Regras de negócio

| # | Regra | Resposta da API quando violada |
|---|-------|--------------------------------|
| RN1 | ISBN-13 com dígito verificador válido (aceita hífens e espaços, que são removidos) | 422 |
| RN2 | ISBN não pode se repetir no acervo | 409 |
| RN3 | CPF não pode se repetir entre leitores | 409 |
| RN4 | Empréstimo só com exemplar disponível (`quantidade_total − empréstimos ativos > 0`) | 409 |
| RN5 | Leitor pode ter no máximo **3** empréstimos ativos | 409 |
| RN6 | Prazo de devolução: **14 dias** a partir do empréstimo | — |
| RN7 | Multa de **R$ 2,00 por dia** de atraso; devolução no prazo tem multa zero | — |
| RN8 | Empréstimo já devolvido não pode ser devolvido de novo | 409 |
| RN9 | Livro com empréstimo ativo não pode ser excluído | 409 |
| RN10 | Quantidade de exemplares não pode ficar menor que os empréstimos ativos | 409 |

Validação de formato (campo obrigatório, e-mail, CPF com 11 dígitos,
quantidade ≥ 1) é feita pelo Pydantic e responde **422**. Recurso inexistente
responde **404**.

## 4. API (JSON)

| Método | Rota | Descrição | Sucesso |
|--------|------|-----------|---------|
| GET | `/api/livros` | Lista livros com `disponiveis` | 200 |
| POST | `/api/livros` | Cadastra livro | 201 |
| GET | `/api/livros/{id}` | Busca livro | 200 |
| PUT | `/api/livros/{id}` | Atualiza livro | 200 |
| DELETE | `/api/livros/{id}` | Exclui livro | 204 |
| GET | `/api/livros/preencher/{isbn}` | Sugere título/autor via OpenLibrary (404 se não achar, 503 se fora do ar) | 200 |
| GET | `/api/leitores` | Lista leitores | 200 |
| POST | `/api/leitores` | Cadastra leitor | 201 |
| GET | `/api/leitores/{id}` | Busca leitor | 200 |
| GET | `/api/emprestimos?ativos=true` | Lista empréstimos (opcionalmente só os ativos) | 200 |
| POST | `/api/emprestimos` | Empresta `{livro_id, leitor_id}` | 201 |
| POST | `/api/emprestimos/{id}/devolucao` | Devolve e calcula multa | 200 |

Documentação interativa gerada pelo FastAPI em `/docs`.

## 5. Interface web

| Página | Conteúdo |
|--------|----------|
| `/` Livros | Formulário (ISBN, botão "Buscar dados pelo ISBN", Título, Autor, Quantidade) e tabela do acervo com botão Excluir |
| `/leitores` Leitores | Formulário (Nome, CPF, E-mail) e tabela de leitores |
| `/emprestimos` Empréstimos | Seleção de livro e leitor, botão Emprestar, tabela de ativos com botão Devolver e aviso da multa |

Erros de regra aparecem no topo da página em uma região `role="alert"`.

## 6. Dependência externa

OpenLibrary (`https://openlibrary.org/isbn/{isbn}.json`), usada só para
sugerir dados no cadastro. Timeout de 5 s. Se falhar, o sistema responde 503
com a orientação de preencher manualmente; o cadastro em si nunca depende dela.

## 7. Requisitos não funcionais avaliados (ISO/IEC 25010)

| Característica (ISO/IEC 25010) | Requisito | Como é verificado |
|---|---|---|
| **Eficiência de desempenho** — comportamento no tempo | p95 do tempo de resposta < 500 ms com 50 usuários simultâneos | Locust (`locustfile.py`), resultados no README |
| **Confiabilidade** — maturidade | Taxa de falhas < 1% sob a mesma carga | Locust |
| **Usabilidade** — acessibilidade | Zero violações WCAG 2.1 níveis A e AA nas três páginas, inclusive no estado de erro | Axe-core via `axe-playwright-python` |
| **Usabilidade** — operabilidade | Todos os formulários operáveis só pelo teclado, em ordem lógica de foco, com link "Pular para o conteúdo" | Playwright (`Tab` + `to_be_focused()`) |
| **Adequação funcional** — correção | Regras RN1–RN10 | Testes de integração (`@pytest.mark.integration`) |
| **Compatibilidade** — interoperabilidade | Falha da OpenLibrary não derruba o cadastro | Testes com `mocker.patch` (sucesso e falha) |
