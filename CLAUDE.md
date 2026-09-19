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

---

# Zona morta

Erros que **já foram cometidos neste projeto**. Cada linha custou tempo real.
Consulte antes de agir na área correspondente.

## Ambiente (Windows + Docker + terminal)

| Armadilha | O que fazer |
|---|---|
| Heredoc grande no Bash quebra com aspas e acentos (`unexpected EOF`) | Escreva o arquivo com a ferramenta de escrita, não com `cat <<EOF` |
| `perl -pi -e` com `\n` na substituição insere **quebra de linha real** e corrompe o arquivo | Use `sed`/`awk`, ou reescreva o arquivo inteiro |
| `docker run -w /app` no Git Bash vira `C:/Program Files/Git/app` | Prefixe `MSYS_NO_PATHCONV=1` |
| Terminal mostra `OlÃ¡` e quadradinho no lugar de emoji | É só exibição do console. **Não "conserte" o dado** — confira no navegador |
| Captura de tela do navegador embutido congela num quadro antigo | Meça com `getBoundingClientRect()` via JS antes de concluir que há bug |
| No navegador embutido, `transform` **não renderiza** (nem inline com `!important`), mas `margin` funciona | Se um deslocamento "não aplica", teste com margem antes de supor que o CSS está errado |
| `getComputedStyle` durante uma transição devolve o **valor inicial**, não o final | Meça posição real com `getBoundingClientRect()` |
| Varrer `querySelectorAll('*')` atrás de quem passa da borda **não enxerga pseudo-elementos** (`::before`/`::after`) — a varredura voltou vazia com a página rolando 279px para o lado | Compare `scrollWidth` com `clientWidth`; para achar o culpado, desligue o suspeito com um `<style>` injetado e meça de novo |
| `docker compose restart frontend` pode deixar o `ng serve` morto | Use `up -d --force-recreate frontend` e aguarde ~45s |

## Angular e Material

| Armadilha | O que fazer |
|---|---|
| `as` em `@else if` **não compila** (`NG5002`) — quebrou o build duas vezes | O alias só vale no `@if` principal: use `@else { @if (x; as y) { … } }` |
| O tema `azure-blue` **não existe** no Material 17 (só do 18 em diante) | Confira `node_modules/@angular/material/prebuilt-themes/` antes de escolher |
| Rota nova acessada direto cai no `/painel` | Espere o `ng serve` recompilar; o curinga `**` engole rota que ainda não existe |
| Tema próprio e páginas maiores estouram o limite de tamanho do build | Ajuste `budgets` no `angular.json` — não é erro de código |
| Crase dentro de comentário nos `styles` inline do componente (que já estão entre crases) **fecha a string** e quebra o build (`TS2304: Cannot find name`) | Nos estilos inline, cite código entre aspas, nunca entre crases |
| Luz ou brilho que sangra para fora do container (`inset` negativo) alarga o documento e a página rola para os lados | Recorte na raiz da página com `overflow-x: clip`. **Não use `hidden`**: ele cria área de rolagem própria e o cabeçalho `sticky` para de grudar |

Use a favor: **estilos globais no `styles.scss` alcançam classes de componente**.
Foi assim que os alvos de toque de todas as telas foram corrigidos de um lugar só.

## Backend e testes

| Armadilha | O que fazer |
|---|---|
| Chave estrangeira `NOT NULL` numa coluna que às vezes não tem dono (o resumo diário não pertence a um cliente) | Deixe `nullable` e use **OUTER JOIN** — com `JOIN` normal a linha some da listagem |
| `TestClient.get()` não aceita `json=` | Só `post`/`patch`/`put` aceitam |
| Substring traiçoeira: a URL `connectionState` **contém** `connect` | Compare o caminho completo (`/instance/connect/`) |
| Texto de exemplo longo passa em validação de tamanho (`gere_uma_chave...` tem 40 caracteres) | Valide contra uma **lista de valores de exemplo**, não só pelo comprimento |

## Sinais de alerta — pare e verifique

Estes são os erros que mais custaram, porque passaram por "pronto":

- **Troquei o `import` mas esqueci de trocar o uso.** A proteção das rotas ficou
  inativa e quase foi declarada concluída. Depois de refatorar, **rode o caso que
  deveria falhar** e veja falhar.
- **Disse "responsivo" sem medir.** A auditoria seguinte achou 28 alvos de toque
  abaixo do mínimo. Medir é barato; supor é caro.
- **Dois estados diferentes ficaram com a mesma cor** ("Paga" e "Pendente", ambos
  verdes). Ao mexer em cor, compare os estados lado a lado.

| Pensamento | Realidade |
|---|---|
| "É uma mudança pequena, não precisa testar" | As três falhas acima vieram de mudanças pequenas |
| "O código compila, então está certo" | Compilar não é funcionar. A proteção inativa compilava |
| "Já testei uma tela, as outras seguem o padrão" | Não seguem. Meça cada uma |
| "A captura de tela parece estranha, deve ser bug" | Confira por medição antes de sair corrigindo o que não está quebrado |

**Antes de dizer "pronto"**, use `superpowers:verification-before-completion`:
rode o comando, leia a saída, e só então afirme.
