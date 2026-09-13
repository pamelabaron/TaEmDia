# Assinatura e controle de acesso pago

Data: 13/09/2026 · Situação: aprovado, pronto para implementar

> **Escopo novo.** Este documento descreve uma funcionalidade que **não consta
> no RFC**. O RFC menciona "mensalidade" apenas ao descrever as vendas dos
> clientes do vendedor, e "SaaS" apenas na análise de concorrentes. A assinatura
> é uma decisão de produto tomada depois, e deve ser apresentada como tal.

---

## Problema

Hoje qualquer pessoa com uma conta Google entra no TáEmDia e usa tudo. Para o
sistema se sustentar como produto, só quem paga deve conseguir **gravar** —
e isso não pode depender do navegador, que o usuário controla.

## Decisões tomadas

| Questão | Decisão |
|---|---|
| Forma de pagamento | Pix com envio de comprovante |
| Quem confere | A administradora, por uma tela dentro do sistema |
| Período de teste | 7 dias para conta nova |
| Preço | R$ 19,90 por mês (30 dias) |
| Onde a regra é aplicada | No backend, em uma dependência única |
| Quem é administradora | Lista de e-mails em variável de ambiente |

---

## 1. Modelo de dados

### `assinatura` — uma linha por vendedor

| Campo | Tipo | Observação |
|---|---|---|
| `id` | UUID | |
| `vendedor_id` | UUID | único, FK para `vendedor` |
| `valido_ate` | date | data em que o acesso de escrita expira |
| `origem` | texto | `teste` ou `pago` |
| `criado_em` | timestamp | |
| `atualizado_em` | timestamp | |

### `pagamento_assinatura` — histórico de comprovantes

| Campo | Tipo | Observação |
|---|---|---|
| `id` | UUID | |
| `vendedor_id` | UUID | FK para `vendedor` |
| `valor` | numeric | valor declarado no envio |
| `arquivo_nome` | texto | nome original, apenas para exibição |
| `arquivo_caminho` | texto | caminho no volume, nunca exposto ao navegador |
| `arquivo_tipo` | texto | tipo de conteúdo validado |
| `situacao` | texto | `pendente`, `aprovado` ou `recusado` |
| `enviado_em` | timestamp | |
| `avaliado_em` | timestamp | nulo enquanto pendente |
| `avaliado_por` | UUID | nulo enquanto pendente |
| `observacao` | texto | motivo da recusa, opcional |

### Status é derivado, nunca gravado

Mesma convenção do status da parcela. Função **pura**, sem banco:

```
hoje <= valido_ate  e origem == "teste"  ->  em_teste
hoje <= valido_ate  e origem == "pago"   ->  ativa
hoje >  valido_ate                       ->  vencida
sem linha de assinatura                  ->  vencida
```

### Regras de vigência

- **RN-A01** — Conta nova nasce com `valido_ate = hoje + 7 dias`, origem `teste`.
- **RN-A02** — Comprovante aprovado soma **30 dias** a `max(hoje, valido_ate)`.
  Quem paga adiantado não perde os dias que ainda tinha.
- **RN-A03** — Comprovante recusado não altera a vigência.
- **RN-A04** — Um vendedor tem no máximo **um** comprovante pendente por vez.

---

## 2. A trava de escrita

Uma dependência nova (`exigir_assinatura_ativa`), irmã de
`get_current_vendedor_id`, aplicada aos endpoints de escrita. Leitura permanece
aberta a qualquer pessoa autenticada.

Quem está vencido recebe **HTTP 402 Payment Required**, com corpo indicando o
motivo. O código 402 existe exatamente para este caso e deixa o tratamento no
frontend uniforme.

### Endpoints protegidos (10)

| Módulo | Endpoint |
|---|---|
| clientes | `POST /clientes` |
| clientes | `PATCH /clientes/{id}` |
| clientes | `DELETE /clientes/{id}` |
| vendas | `POST /vendas` |
| vendas | `POST /parcelas/{id}/pagar` |
| vendas | `POST /vendas/{id}/cancelar` |
| cobranças | `POST /cobrancas/{id}/disparar` |
| cobranças | `POST /whatsapp/desconectar` |
| configurações | `PATCH /configuracoes` |
| templates | `PATCH /templates/{id}` |

### Exceções deliberadas

| Endpoint | Por quê |
|---|---|
| `POST /auth/google` | é o login |
| `POST /whatsapp/webhook` | é a resposta do devedor, não do assinante |
| `POST /templates/preview` | só monta texto, não grava |
| `POST /assinatura/comprovante` | é como a pessoa volta a ter acesso |

### Por que não dá para burlar

A verificação lê o `vendedor_id` do token assinado e consulta o banco no
servidor. O navegador não participa da decisão: esconder um botão é só conforto
visual. Chamar o endpoint direto, por qualquer ferramenta, devolve 402.

### Rede de segurança

Um teste percorre **todas as rotas registradas no aplicativo** e falha se uma
rota de escrita não estiver na lista de protegidas nem na de exceções. Endpoint
de escrita novo que ninguém protegeu **quebra a suíte**.

Isso responde ao único risco da abordagem escolhida: esquecer de aplicar a
dependência num endpoint futuro.

---

## 3. Administradora

A lista de administradores fica em `ADMIN_EMAILS` (variável de ambiente,
separada por vírgula). Não existe coluna `administrador` no banco — assim
ninguém vira admin por gravação, e não há bit para inverter.

Valor inicial: `p.baron@catolicasc.edu.br`.

Dependência `exigir_admin`: compara o e-mail do vendedor do token com a lista.
Fora dela, **403**.

### Tela `/assinaturas` (somente admin)

- Lista de comprovantes pendentes: quem enviou, valor, data, arquivo.
- Botões **Aprovar** e **Recusar** (recusa pede motivo).
- Aprovar aplica a RN-A02; recusar aplica a RN-A03.

### Armazenamento dos comprovantes

- Volume do Docker (`uploads-data`), fora de qualquer pasta servida como
  estática — nenhum arquivo enviado é alcançável por URL pública.
- Download só pelo endpoint `GET /admin/comprovantes/{id}/arquivo`, autenticado
  e restrito a admin.
- Aceitos: `image/jpeg`, `image/png`, `application/pdf`. Máximo **5 MB**.
- O tipo é validado pelo **conteúdo** do arquivo, não pela extensão do nome.
- O nome do arquivo salvo é gerado pelo sistema (UUID); o nome original é
  guardado apenas como texto de exibição, nunca usado para montar caminho.

---

## 4. Tela "Minha assinatura" (dentro de Configurações)

- Situação atual (Em teste / Ativa / Vencida) e até quando vale.
- Valor: R$ 19,90 por mês.
- Chave Pix (vem de `PIX_CHAVE`, variável de ambiente) com botão de copiar.
- Envio do comprovante: valor e arquivo.
- Histórico dos envios com a situação de cada um.

Enquanto houver comprovante pendente, o formulário informa que já existe um
envio em análise (RN-A04) em vez de aceitar outro.

---

## 5. Comportamento no frontend

- **Navegar continua livre.** Painel, clientes, ranking, cobranças e mensagens
  seguem visíveis para quem está vencido. O sistema não vira uma parede.
- Um interceptor trata o **402** de forma única: abre um aviso com
  *"Sua assinatura venceu. Renove para continuar."* e link para Configurações.
- Faixa discreta no topo quando o teste está nos últimos dias, e quando vencido.
- Botões de ação continuam visíveis; quem clica recebe o aviso. Esconder botões
  daria a impressão de sistema quebrado.

---

## 6. Testes

| O quê | Como |
|---|---|
| Derivação do status | função pura, sem banco — casos de borda em `valido_ate` |
| RN-A02 (soma de 30 dias) | função pura, incluindo pagamento adiantado |
| Cobertura da trava | varredura de todas as rotas registradas |
| 402 para vencido | cliente de teste em cada endpoint protegido |
| Leitura liberada | vencido continua lendo painel e clientes |
| 403 para não-admin | tentativa de acessar a tela e o download |
| Upload | tipo inválido, arquivo grande demais, segundo envio pendente |
| Isolamento | admin de uma conta não enxerga dados de outra (RNF07) |

---

## Fora de escopo

- Gateway de pagamento e renovação automática. O desenho comporta a troca
  depois: basta uma origem nova de aprovação chamando a mesma regra da RN-A02.
- Cobrança proporcional, cupons, planos diferentes, faturamento e nota fiscal.
- Reembolso e cancelamento com devolução.
