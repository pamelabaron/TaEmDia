# TáEmDia — instruções para o Claude

Sistema web de cobrança automatizada via WhatsApp e gestão de carteira de clientes.
Projeto de TCC — Engenharia de Software, Católica SC. Autora: Pâmela Baron.

O **RFC é a fonte de verdade** dos requisitos. Ao implementar algo, cite o
requisito correspondente (RF, RNF ou RN) nos comentários e na mensagem de commit.

---

## Use as skills do superpowers

**Antes de responder ou agir**, verifique se alguma skill se aplica e invoque-a —
inclusive antes de fazer perguntas de esclarecimento ou explorar o código.
Anuncie "Usando [skill] para [objetivo]" e siga a skill.

Skills de **processo** vêm primeiro (definem a abordagem); as de **implementação**
depois executam.

| Situação | Skill |
|---|---|
| Criar funcionalidade, componente ou mudar comportamento | `superpowers:brainstorming` **antes de codar** |
| Implementar qualquer feature ou correção | `superpowers:test-driven-development` |
| Bug, teste falhando, comportamento inesperado | `superpowers:systematic-debugging` **antes de propor solução** |
| Antes de afirmar que está pronto, corrigido ou passando | `superpowers:verification-before-completion` |
| Tarefa de várias etapas com requisitos definidos | `superpowers:writing-plans` → `superpowers:executing-plans` |
| Concluir uma etapa ou antes de integrar | `superpowers:requesting-code-review` |
| Ao receber retorno de revisão | `superpowers:receiving-code-review` |
| Encerrar uma linha de trabalho | `superpowers:finishing-a-development-branch` |
| Tarefas independentes que dão para paralelizar | `superpowers:dispatching-parallel-agents` |

Se houver 1% de chance de uma skill se aplicar, invoque. "É simples demais",
"preciso de contexto antes" e "deixa eu só olhar os arquivos" são sinais de que
você está racionalizando para pular a skill.

## Interface e design

Para qualquer trabalho visual (telas, responsividade, tipografia, cor, layout,
acessibilidade), use `impeccable:impeccable` — cobre `adapt`, `polish`,
`critique`, `audit`, entre outros.

---

## Como rodar

Tudo sobe com Docker, em um comando:

```bash
docker compose up
```

- Interface: http://localhost:4200
- API: http://localhost:8000 · documentação em `/docs`

Detalhes em [COMO-RODAR.md](COMO-RODAR.md).

## Testes

```bash
docker compose exec backend pytest
```

Meta do RFC: **75% de cobertura** no backend (hoje em 91%, 262 testes).
Escreva as regras de negócio como **funções puras** sempre que possível — é o que
mantém a suíte rápida e a cobertura alta. Ver [docs/testes.md](docs/testes.md).

## Frontend

O host não tem Node no PATH; rode o Angular por container:

```bash
docker run --rm -v "%cd%\frontend:/app" -w /app node:20 npx ng build
```

No Git Bash, prefixe com `MSYS_NO_PATHCONV=1` para o `-w /app` não ser convertido.

## Convenções do projeto

- **Backend em camadas**: `router` (HTTP) → `service` (regras) → `repository`
  (única camada que toca o banco). Nunca pule uma camada.
- **Isolamento entre contas**: toda consulta filtra por `vendedor_id`. É requisito
  de segurança (RNF07), não detalhe de implementação.
- **Status da parcela é derivado**, nunca armazenado — calculado a partir das datas.
- **Cores com significado**: verde = pago, laranja = atraso, vermelho =
  inadimplente, cinza neutro = pendente. Não use verde para "pendente".
- **Tamanho de alvo de toque** é decidido por `@media (pointer: coarse)`, não por
  largura de tela.
- Código, comentários e mensagens de commit **em português**.

## Ao terminar

- Rode os testes e confirme a saída antes de dizer que está pronto.
- **Limpe os dados de teste** do banco (contas de teste usam e-mails `@teste.local`).
- Nunca versione `.env` nem certificados.
