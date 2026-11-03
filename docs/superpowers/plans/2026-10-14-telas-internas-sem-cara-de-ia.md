# Telas internas sem cara de IA. Plano de implementação

> **Para quem for executar:** use `superpowers:subagent-driven-development` ou
> `superpowers:executing-plans`. Os passos usam caixas (`- [ ]`) para marcar.

**Objetivo:** tirar das 10 telas internas os padrões que denunciam interface
gerada por máquina, mantendo o tema ameixa escuro e sem piorar a leitura de
quem usa o sistema todo dia.

**Abordagem:** três frentes, nesta ordem. Primeiro os estados que hoje não
existem (vazio, erro, carregando), porque é o que mais separa sistema acabado
de protótipo. Depois a hierarquia (um número principal no painel, uma ação
principal por tela). Por último o ritmo de espaçamento e a cópia.

**Tecnologias:** Angular 17, Angular Material 17, Karma e Jasmine, pytest para
as varreduras que leem arquivo.

**Base da decisão:** pesquisa sobre padrões genéricos de IA em interface de
sistema, resumida na seção "Os sete sinais" abaixo.

## Restrições do projeto

- Tema **ameixa escuro** mantido. Cores só por token do `styles.scss`; nenhuma
  tela escreve cor fixa.
- Cores de estado conservam o significado: verde pago, laranja atraso, vermelho
  inadimplente, cinza pendente. No escuro elas são claras, então o que for
  pintado com elas leva texto escuro (`var(--fundo-900)`).
- Código, comentários e mensagens de commit **em português**.
- **Nunca usar travessão** em texto nenhum.
- Alvo de toque decidido por `@media (pointer: coarse)`, não por largura.
- Cobertura do frontend não pode cair abaixo de **25%** nas quatro medidas.
- Nenhuma afirmação de fato pode mudar sem a autora aprovar. Rótulo e mensagem
  de erro podem ser reescritos; número, percentual e promessa, não.

## Os sete sinais, e onde cada um aparece aqui

| Sinal | Situação no TáEmDia |
|---|---|
| 1. Todo cartão com o mesmo peso | **Painel**: quatro cartões iguais, nenhum número principal |
| 2. Componente com estilo de fábrica | Já tratado: cartão, botão e campo têm estilo próprio |
| 3. Toda tela é o mesmo painel | A conferir por tela na Tarefa 6 |
| 4. Espaçamento uniforme, sem ritmo | A medir na Tarefa 7 |
| 5. Vazio, erro e carregando genéricos | **O maior buraco.** Detalhado abaixo |
| 6. Cópia de preenchimento | 10 mensagens no formato "Erro ao ..." |
| 7. Sem ponto focal | **Clientes**: 2 de 2 botões primários. **Perfil**: 3 de 6 |

### Detalhe do sinal 5, por tela

| Tela | Vazio | Erro | Carregando |
|---|---|---|---|
| Painel | uma linha de texto | aviso de rodapé | roda girando |
| Clientes | uma linha de texto | aviso de rodapé | roda girando |
| Perfil do cliente | uma linha de texto | aviso de rodapé | roda girando |
| Cobranças | uma linha de texto | aviso de rodapé | roda girando |
| Mensagens | **nenhum** | aviso de rodapé | roda girando |
| WhatsApp | **nenhum** | aviso de rodapé | **nenhum** |
| Cobrança automática | **nenhum** | aviso de rodapé | roda girando |
| Resumo diário | uma linha de texto | aviso de rodapé | roda girando |
| Minha assinatura | uma linha de texto | aviso de rodapé | roda girando |
| Comprovantes | uma linha de texto | aviso de rodapé | roda girando |

"Uma linha de texto" é literalmente isto: `Nenhum cliente cadastrado ainda.`
em cinza, centralizado. Não diz o que fazer em seguida.

"Aviso de rodapé" é a tarja preta que sobe por 4 segundos escrito
`Erro ao carregar clientes.` A pessoa fica com a tela vazia e sem saber se
tenta de novo, se a internet caiu ou se o sistema quebrou.

---

## Estrutura de arquivos

**Criar:**

- `frontend/src/app/core/estado-vazio.component.ts` — o componente de tela
  vazia: título, uma frase, e um botão de ação. Um só, usado por todas.
- `frontend/src/app/core/estado-erro.component.ts` — o painel de erro no lugar
  do conteúdo: o que houve, o que fazer, e o botão "Tentar de novo".
- `frontend/src/app/core/esqueleto.component.ts` — o esqueleto de carregamento,
  que desenha a forma do conteúdo que está vindo.
- `frontend/src/app/estados-das-telas.spec.ts` — monta cada tela nos três
  estados e reprova quem não tiver estado desenhado.

**Modificar:** as 10 telas de `frontend/src/app/pages/`, mais o
`frontend/src/styles.scss` para os tokens de ritmo de espaçamento.

---

## Tarefa 1: O teste que prova a falta

Antes de escrever componente nenhum, o teste que mostra quais telas não têm
estado desenhado. Sem ele, "arrumei os estados" é opinião.

**Arquivos:**
- Criar: `frontend/src/app/estados-das-telas.spec.ts`

**Produz:** `TELAS_COM_ESTADO`, a lista de telas conferidas, consumida pelas
tarefas seguintes para saber o que já foi feito.

- [ ] **Passo 1: escrever o teste que falha**

Para cada tela, monta o componente, responde a chamada com lista vazia, e
exige que exista um elemento com `data-estado="vazio"` contendo um título,
uma explicação e uma ação.

```typescript
it(`a tela "${nome}" tem estado vazio desenhado`, () => {
  const fixture = montar(componente, { vazio: true });
  const vazio = fixture.nativeElement.querySelector('[data-estado="vazio"]');

  expect(vazio).withContext('não existe estado vazio').not.toBeNull();
  expect(vazio.querySelector('h3')?.textContent?.trim()).toBeTruthy();
  expect(vazio.querySelector('p')?.textContent?.trim()).toBeTruthy();
  expect(vazio.querySelector('button, a')).withContext('sem próxima ação').not.toBeNull();
});
```

- [ ] **Passo 2: rodar e ver falhar**

```bash
docker compose --profile testes run --rm frontend-testes
```

Esperado: 10 falhas, uma por tela, todas em "não existe estado vazio".

- [ ] **Passo 3: commitar o teste que falha**

```bash
git add frontend/src/app/estados-das-telas.spec.ts
git commit -m "Teste dos estados das telas"
```

---

## Tarefa 2: O componente de tela vazia

**Arquivos:**
- Criar: `frontend/src/app/core/estado-vazio.component.ts`
- Teste: o da Tarefa 1

**Consome:** nada. **Produz:** `<app-estado-vazio titulo texto acao (aoAgir)>`.

- [ ] **Passo 1: escrever o componente**

```typescript
@Component({
  selector: 'app-estado-vazio',
  standalone: true,
  imports: [MatButtonModule, MatIconModule],
  template: `
    <div class="vazio" data-estado="vazio">
      <h3>{{ titulo }}</h3>
      <p>{{ texto }}</p>
      @if (acao) {
        <button mat-flat-button color="primary" (click)="aoAgir.emit()">
          {{ acao }}
        </button>
      }
    </div>
  `,
})
export class EstadoVazioComponent {
  @Input({ required: true }) titulo = '';
  @Input({ required: true }) texto = '';
  @Input() acao = '';
  @Output() aoAgir = new EventEmitter<void>();
}
```

- [ ] **Passo 2: usar nas 10 telas, com texto próprio de cada uma**

O texto **não é genérico**. Cada tela diz o que aquela tela faz e qual é o
próximo passo. Exemplos para usar, um por tela:

| Tela | Título | Texto | Ação |
|---|---|---|---|
| Clientes | Sua carteira começa aqui | Cadastre quem compra parcelado e o sistema passa a cuidar dos vencimentos. | Cadastrar cliente |
| Painel | Nada a receber ainda | Os números aparecem quando você registrar a primeira venda. | Ver clientes |
| Perfil | Nenhuma venda para este cliente | Registre a primeira venda e o sistema calcula as parcelas. | Registrar venda |
| Cobranças | Nenhuma cobrança neste período | Troque o período acima, ou espere a próxima data de envio. | (sem ação) |
| Mensagens | Os modelos ainda não carregaram | Cada tipo de cobrança tem um texto que você pode mudar. | Recarregar |
| WhatsApp | Nenhum número conectado | Conecte um número para o sistema poder enviar as cobranças. | Conectar |
| Resumo diário | Nenhuma atividade neste dia | Escolha outro dia acima, ou volte amanhã. | (sem ação) |
| Minha assinatura | Nenhum pagamento enviado | Quando você enviar um comprovante, ele aparece aqui. | (sem ação) |
| Comprovantes | Nada para avaliar | Comprovantes enviados pelos vendedores chegam nesta fila. | (sem ação) |
| Cobrança automática | (não se aplica: é formulário) | | |

- [ ] **Passo 3: rodar o teste e ver passar**

- [ ] **Passo 4: commitar**

```bash
git commit -am "Tela vazia com proxima acao"
```

---

## Tarefa 3: O painel de erro no lugar do aviso de rodapé

A tarja que sobe e some em 4 segundos é o pior lugar para um erro de
carregamento: ela desaparece sozinha e deixa a pessoa olhando para o nada.

**Arquivos:**
- Criar: `frontend/src/app/core/estado-erro.component.ts`
- Modificar: as 10 telas, trocando `snack.open('Erro ao ...')` por estado.

- [ ] **Passo 1: escrever o teste que falha**

```typescript
it(`a tela "${nome}" explica o erro e oferece saída`, () => {
  const fixture = montar(componente, { erro: 500 });
  const erro = fixture.nativeElement.querySelector('[data-estado="erro"]');

  expect(erro).not.toBeNull();
  expect(erro.querySelector('button')?.textContent).toContain('Tentar de novo');
});
```

- [ ] **Passo 2: escrever o componente**

```typescript
@Component({
  selector: 'app-estado-erro',
  standalone: true,
  imports: [MatButtonModule, MatIconModule],
  template: `
    <div class="erro" data-estado="erro">
      <h3>{{ titulo }}</h3>
      <p>{{ texto }}</p>
      <button mat-stroked-button (click)="aoTentar.emit()">Tentar de novo</button>
    </div>
  `,
})
export class EstadoErroComponent {
  @Input() titulo = 'Não deu para carregar';
  @Input() texto = 'Pode ter sido a conexão. O que estava salvo continua lá.';
  @Output() aoTentar = new EventEmitter<void>();
}
```

- [ ] **Passo 3: substituir as 10 mensagens genéricas**

As que existem hoje, e que saem: `Erro ao carregar clientes.`,
`Erro ao carregar as cobranças.`, `Erro ao carregar mensagens.`,
`Erro ao carregar o cliente.`, `Erro ao salvar.`, e as demais do mesmo formato.
A tarja continua existindo só para erro de **ação** (salvar, cancelar), onde a
tela já tem conteúdo e a pessoa não ficou sem nada.

- [ ] **Passo 4: rodar os testes e ver passar**

- [ ] **Passo 5: commitar**

```bash
git commit -am "Erro explicado na tela, com saida"
```

---

## Tarefa 4: Esqueleto no lugar da roda girando

**Arquivos:**
- Criar: `frontend/src/app/core/esqueleto.component.ts`
- Modificar: as 9 telas que hoje mostram `mat-spinner`.

- [ ] **Passo 1: escrever o teste que falha**

```typescript
it(`a tela "${nome}" mostra a forma do que está vindo`, () => {
  const fixture = montar(componente, { pendente: true });
  expect(fixture.nativeElement.querySelector('[data-estado="carregando"]')).not.toBeNull();
  expect(fixture.nativeElement.querySelector('mat-spinner'))
    .withContext('ainda usa roda girando').toBeNull();
});
```

- [ ] **Passo 2: escrever o componente**

Barras com a altura e a largura aproximadas do conteúdo real, com animação de
brilho que respeita `prefers-reduced-motion`.

- [ ] **Passo 3: trocar nas 9 telas, com a forma de cada conteúdo**

Lista de clientes: linhas. Painel: blocos de número. Resumo: blocos de número.

- [ ] **Passo 4: rodar e ver passar.** **Passo 5: commitar.**

---

## Tarefa 5: Um número principal no painel

Quatro cartões do mesmo tamanho dizem que existem quatro coisas, não qual
importa. Num sistema de cobrança, o que exige ação é **o valor em atraso**.

**Arquivos:**
- Modificar: `frontend/src/app/pages/dashboard/dashboard.component.ts`

- [ ] **Passo 1: escrever o teste que falha**

```typescript
it('o painel tem um número que domina os outros', () => {
  const fixture = montarPainel();
  const tamanhos = [...fixture.nativeElement.querySelectorAll('.kpi .valor')]
    .map((e: Element) => parseFloat(getComputedStyle(e).fontSize));
  const maior = Math.max(...tamanhos);
  const resto = tamanhos.filter((t) => t !== maior);

  expect(maior).toBeGreaterThan(Math.max(...resto) * 1.4);
});
```

- [ ] **Passo 2: dar ao "em atraso" a largura dupla e o corpo maior**

- [ ] **Passo 3: rodar e ver passar.** **Passo 4: commitar.**

---

## Tarefa 6: Uma ação principal por tela

**Arquivos:**
- Modificar: `clientes.component.ts` (2 de 2 primários),
  `cliente-perfil.component.ts` (3 de 6 primários).

- [ ] **Passo 1: escrever a varredura que falha**

Em pytest, lendo os arquivos, como as outras varreduras do projeto:

```python
def test_cada_tela_tem_uma_acao_principal(telas):
    demais = [
        f"{arquivo}: {n} botões primários"
        for arquivo, n in telas.items() if n > 1
    ]
    assert not demais, (
        "Telas com mais de um botão primário: " + ", ".join(demais)
        + ". Mais de uma ação principal é o mesmo que nenhuma."
    )
```

- [ ] **Passo 2: rebaixar os secundários para `mat-stroked-button`**

- [ ] **Passo 3: rodar e ver passar.** **Passo 4: commitar.**

---

## Tarefa 7: Ritmo de espaçamento

Vão igual em tudo é o espaçamento que ninguém escolheu.

**Arquivos:**
- Modificar: `frontend/src/styles.scss` (tokens), as 10 telas (uso).

- [ ] **Passo 1: criar a escala**

```scss
--vao-dentro: 8px;    /* entre itens do mesmo grupo */
--vao-grupo: 20px;    /* entre grupos de uma seção */
--vao-secao: 44px;    /* entre seções */
```

- [ ] **Passo 2: aplicar, apertando dentro do grupo e abrindo entre grupos**

- [ ] **Passo 3: medir com `getBoundingClientRect()` e confirmar.**
- [ ] **Passo 4: commitar.**

---

## Tarefa 8: Cópia de cada tela

**Arquivos:** as 10 telas.

- [ ] **Passo 1: trocar rótulo genérico por rótulo que nomeia a coisa**

Nenhum número, percentual ou promessa muda. Só rótulo de botão, título de
seção e mensagem de erro.

- [ ] **Passo 2: commitar.**

---

## Tarefa 9: Conferência final

- [ ] Contraste de todo texto, nas 10 telas, pela medição do
      `tema-escuro.spec.ts`
- [ ] Sem rolagem lateral em 320, 375, 768, 1280 e 1920px
- [ ] Alvo de toque mínimo de 44px no toque
- [ ] `impeccable detect` sem achados
- [ ] `docker compose exec backend pytest` todo verde
- [ ] `docker compose --profile testes run --rm frontend-testes` verde e acima
      de 25% nas quatro medidas
- [ ] Build de produção completo

---

## Ordem sugerida e tamanho

As tarefas 1 a 4 são o grosso do valor: são elas que tiram a impressão de
protótipo. As tarefas 5 a 8 são refinamento.

Cada tarefa fecha com teste e commit próprios, então dá para parar entre
qualquer uma delas sem deixar o sistema pela metade.
