# Relatório de uso de IA

## Ferramenta

**Claude Code** (modelo Claude Opus 5.5, da Anthropic), usado no terminal
do WSL com acesso ao diretório do projeto.

## Onde a IA foi usada

| Etapa | Uso |
|-------|-----|
| Planejamento | Leitura do enunciado, sugestão do domínio (biblioteca) e das regras de negócio, documento de design e plano de implementação (`docs/superpowers/`) |
| Código da aplicação | Geração de `app/` (rotas, repositório, regras, serviço externo, templates, CSS) |
| Testes | Geração das factories, fixtures, testes de integração, Page Objects, testes E2E e de acessibilidade, `locustfile.py` |
| Documentação | Rascunho de `PRD.md`, `AGENTS.md`, `README.md` e deste arquivo |

Os testes de **integração** foram feitos em TDD: a IA escreveu os testes,
executou e mostrou que falhavam, e só então escreveu o código. Os testes
**E2E e de acessibilidade** foram escritos depois das páginas prontas, então
nem todos foram vistos falhando antes — os 3 que falharam foram justamente os
que revelaram o bug do item 3 abaixo. O histórico de commits mostra uma etapa
por commit.

## Como o resultado foi auditado

O que foi conferido com evidência, e não apenas aceito:

1. **Dígito verificador do ISBN de exemplo.** O plano inicial trazia
   `978-85-359-0277-5` como ISBN válido. O dígito foi recalculado à mão
   (soma ponderada 1/3 = 142 → dígito 8) e o plano estava **errado**;
   corrigido para `...277-8` antes de virar teste.
2. **Formato real da OpenLibrary.** Os testes usam mock, então não provam que
   a API real responde no formato assumido. Foi feita uma chamada real única
   (ISBN 9780140449136) que retornou `{'titulo': 'Crime and punishment',
   'autor': 'Fiódor Dostoievski'}`, confirmando o formato (autor vem como
   chave e exige segunda chamada).
3. **Bug de commit após a resposta, encontrado pelo E2E.** Os testes de
   integração passavam, mas o E2E mostrou que, depois de cadastrar um livro
   pela página, ele não aparecia na tabela. Causa: o `commit()` no `yield`
   da dependência rodava **depois** de a resposta ser enviada (padrão do
   FastAPI), e o navegador pedia a página antes do commit. Corrigido com
   `Depends(..., scope="function")`. O código gerado pela IA tinha o bug; foi
   o teste que o encontrou.
4. **Condição de corrida no empréstimo.** Identificado na revisão que duas
   requisições simultâneas poderiam emprestar o último exemplar; corrigido
   com `BEGIN IMMEDIATE`.
5. **Revisão independente.** Ao final, uma segunda instância do modelo, sem
   ter escrito o código, revisou o projeto inteiro e rodou testes de
   concorrência reais (20 empréstimos simultâneos do último exemplar: 1 aceito,
   19 recusados). Ela apontou, entre outros, que este arquivo exagerava o uso
   de TDD e que os números do README não batiam com o CSV — ambos corrigidos.
6. **Estabilidade.** A suíte completa foi executada 3 vezes seguidas com 100%
   de aprovação antes de ser considerada pronta.
7. **Números de carga.** Os valores no README foram copiados de
   `resultados/carga_stats.csv`, de uma execução real do Locust.
