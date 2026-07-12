# Modelo de Dados — TáEmDia

> Este documento preenche a Seção 5.2 do RFC (que estava sem detalhamento).
> Banco relacional **PostgreSQL**. Valores monetários em `DECIMAL(10,2)`.
> Regra transversal de segurança: **toda** tabela de dados operacionais carrega
> (direta ou indiretamente) o `vendedor_id`, e toda consulta filtra por ele
> (isolamento entre contas — RNF07 / RN02).

## Visão geral das entidades

| Entidade            | Descrição                                                        |
|---------------------|------------------------------------------------------------------|
| `vendedor`          | Dono da conta. Criado no 1º login Google. Um número de WhatsApp. |
| `configuracao`      | Preferências do agente por vendedor (1-para-1 com vendedor).     |
| `cliente`           | Devedor cadastrado na carteira de um vendedor.                   |
| `venda`             | Uma compra parcelada de um cliente.                              |
| `parcela`           | Cada parcela de uma venda, com vencimento e status.             |
| `template_mensagem` | Modelos de mensagem de cobrança (padrão ou personalizados).     |
| `cobranca_log`      | Registro de cada mensagem de cobrança enviada.                   |
| `resposta_devedor`  | Resposta numerada (1/2/3) recebida do devedor.                  |

## Diagrama de relacionamentos (texto)

```
vendedor (1) ─── (1) configuracao
vendedor (1) ─── (N) cliente
vendedor (1) ─── (N) template_mensagem
cliente  (1) ─── (N) venda
venda    (1) ─── (N) parcela
parcela  (1) ─── (N) cobranca_log
parcela  (1) ─── (N) resposta_devedor
```

## Tabelas

### vendedor
| Coluna            | Tipo          | Regras                                            |
|-------------------|---------------|---------------------------------------------------|
| id                | UUID (PK)     | gerado pelo sistema                               |
| google_email      | VARCHAR único | identificador de login (RF01/RF02)                |
| nome              | VARCHAR       | vindo do perfil Google                            |
| whatsapp_numero   | VARCHAR null  | número conectado via QR Code (Evolution API)      |
| ativo             | BOOLEAN       | soft delete da conta                              |
| criado_em         | TIMESTAMP     |                                                   |

### configuracao (1-para-1 com vendedor)
| Coluna                      | Tipo         | Regras                                        |
|-----------------------------|--------------|-----------------------------------------------|
| id                          | UUID (PK)    |                                               |
| vendedor_id                 | UUID (FK) único |                                            |
| dias_antecedencia_lembrete  | INT          | quantos dias antes do vencimento avisar (RF)  |
| horario_resumo              | TIME         | horário do resumo diário (RF)                 |
| resumo_ativo                | BOOLEAN      | liga/desliga resumo diário (RF)               |
| envio_auto_global           | BOOLEAN      | chave geral do envio automático               |

### cliente
| Coluna               | Tipo          | Regras                                              |
|----------------------|---------------|-----------------------------------------------------|
| id                   | UUID (PK)     |                                                     |
| vendedor_id          | UUID (FK)     | isolamento por conta                                |
| nome                 | VARCHAR       | obrigatório (RF04)                                  |
| whatsapp_numero      | VARCHAR       | obrigatório; **único por vendedor** (RF05/RN04/RN05)|
| cpf                  | VARCHAR null  | opcional                                            |
| endereco             | VARCHAR null  | opcional                                            |
| envio_auto_ativo     | BOOLEAN       | envio automático por cliente (RF / RN11)            |
| interacao_habilitada | BOOLEAN       | permite opções de resposta 1/2/3 (RF)               |
| ativo                | BOOLEAN       | soft delete — preserva histórico                    |
| criado_em            | TIMESTAMP     |                                                     |

**Restrição:** `UNIQUE (vendedor_id, whatsapp_numero)`.

### venda
| Coluna                | Tipo            | Regras                                        |
|-----------------------|-----------------|-----------------------------------------------|
| id                    | UUID (PK)       |                                               |
| vendedor_id           | UUID (FK)       | redundante p/ isolamento e queries rápidas    |
| cliente_id            | UUID (FK)       |                                               |
| valor_total           | DECIMAL(10,2)   | mínimo R$ 1,00 (RN06)                          |
| num_parcelas          | INT             | 1 a 60 (RN07)                                 |
| data_primeira_parcela | DATE            | base do cálculo de vencimentos                |
| status                | ENUM            | `ativa`, `cancelada` (RF cancelar venda)      |
| criado_em             | TIMESTAMP       |                                               |

### parcela
| Coluna          | Tipo          | Regras                                                     |
|-----------------|---------------|------------------------------------------------------------|
| id              | UUID (PK)     |                                                            |
| venda_id        | UUID (FK)     |                                                            |
| numero_parcela  | INT           | 1..N                                                       |
| valor           | DECIMAL(10,2) | valor_total / num_parcelas                                 |
| data_vencimento | DATE          | calculado (mês a mês a partir da 1ª parcela)               |
| data_pagamento  | DATE null     | preenchido só quando o vendedor confirma                   |
| status          | ENUM          | `pendente`, `atrasada`, `aguardando_confirmacao`, `paga`   |
| criado_em       | TIMESTAMP     |                                                            |

**Ciclo de vida (Seção 3.1.2 do RFC):**
`pendente` → `atrasada` (dia seguinte ao vencimento, automático) →
`aguardando_confirmacao` (devedor responde "1 – já paguei") →
`paga` (só o vendedor confirma). Ver RN09 e RN13.

### template_mensagem
| Coluna      | Tipo      | Regras                                                    |
|-------------|-----------|-----------------------------------------------------------|
| id          | UUID (PK) |                                                           |
| vendedor_id | UUID (FK) | null = template padrão do sistema                         |
| tipo        | ENUM      | `lembrete`, `vencimento`, `atraso`                        |
| titulo      | VARCHAR   |                                                           |
| corpo       | TEXT      | variáveis: `{nome_cliente} {valor_parcela} {data_vencimento} {dias_atraso}` |
| is_padrao   | BOOLEAN   | template pré-configurado                                  |
| ativo       | BOOLEAN   |                                                           |

### cobranca_log
| Coluna      | Tipo       | Regras                                              |
|-------------|------------|-----------------------------------------------------|
| id          | UUID (PK)  |                                                     |
| vendedor_id | UUID (FK)  | isolamento                                          |
| cliente_id  | UUID (FK)  |                                                     |
| parcela_id  | UUID (FK)  |                                                     |
| tipo        | ENUM       | `lembrete`, `vencimento`, `atraso`, `manual`, `resumo` |
| conteudo    | TEXT       | mensagem efetivamente enviada                       |
| status      | ENUM       | `enviado`, `falhou`, `pendente` (fila de reenvio)   |
| enviado_em  | TIMESTAMP null |                                                 |
| criado_em   | TIMESTAMP  |                                                     |

### resposta_devedor
| Coluna      | Tipo      | Regras                                                   |
|-------------|-----------|----------------------------------------------------------|
| id          | UUID (PK) |                                                          |
| parcela_id  | UUID (FK) | parcela em aberto mais antiga do cliente (RN14)          |
| cliente_id  | UUID (FK) |                                                          |
| opcao       | ENUM      | `1_ja_paguei`, `2_pago_hoje`, `3_nao_consigo`            |
| recebido_em | TIMESTAMP |                                                          |

> **Ranking (Bom Pagador / Regular / Inadimplente)** é **derivado** — calculado
> pelo Ranking Service a partir de parcelas/pagamentos dos últimos 12 meses
> (RN15/RN16). Pode ser recalculado a cada confirmação de pagamento e,
> opcionalmente, cacheado numa coluna `classificacao` em `cliente` no futuro.
