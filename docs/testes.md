# Testes Automatizados

O backend é coberto por testes automatizados com **pytest**, conforme exigido no
RFC (cobertura mínima de 75% no backend).

## Como rodar

Com o sistema no ar (`docker compose up`), execute:

```bash
docker compose exec backend pytest
```

Isso roda toda a suíte e mostra o relatório de cobertura no terminal.

Para rodar só um arquivo:

```bash
docker compose exec backend pytest tests/test_ranking.py
```

## Resultado atual

| Métrica | Valor |
|---|---|
| Testes | **218** |
| Cobertura do backend | **90%** |
| Meta do RFC | 75% ✅ |

O relatório detalhado em HTML fica em `backend/htmlcov/index.html` (abra no
navegador) e o `backend/coverage.xml` é o formato lido pelo SonarCloud.

## O que é testado

| Arquivo | O que cobre |
|---|---|
| `test_regras_cobranca.py` | Horário comercial (RN11), escolha do template por data, variáveis da mensagem, opções de resposta, limite diário (RN10) |
| `test_ranking.py` | Classificação bom/regular/inadimplente/sem histórico (RN15/RN16) |
| `test_vendas_calculos.py` | Divisão em parcelas (centavos), vencimentos mensais (fim de mês, ano bissexto), status da parcela (RN09) |
| `test_templates.py` | Substituição de variáveis e templates padrão |
| `test_security.py` | Emissão e validação do token de sessão (JWT) |
| `test_api_clientes.py` | Cadastro, WhatsApp único (RF05), soft delete e **isolamento entre contas** (RNF07) |
| `test_api_vendas.py` | Registro de venda, validações (RN06/RN07), pagamento, cancelamento e saldo devedor |
| `test_api_cobrancas.py` | Disparo manual, varredura automática e as regras de envio |
| `test_agente.py` | Respostas 1/2/3 do devedor, texto livre ignorado, resposta duplicada e resumo diário |
| `test_api_configuracoes.py` | Configurações do agente e validação de faixa |
| `test_api_relatorios.py` | Painel financeiro (KPIs) e ranking |
| `test_api_templates.py` | API de templates e prévia |
| `test_whatsapp_client.py` | Simulador e Evolution API (com respostas simuladas) |

## Como funciona

- Os testes usam um **banco separado** (`taemdia_test`), criado automaticamente.
  Os dados reais nunca são tocados.
- Cada teste começa com o banco limpo.
- O agendador de tarefas fica desligado durante os testes.
- Nenhuma mensagem de WhatsApp é enviada de verdade: usa-se o simulador.

## Testes do frontend

```bash
docker compose --profile testes run --rm frontend-testes
```

Roda num container com Chromium embutido (`docker/frontend-testes.Dockerfile`),
sem instalar nada no computador. Na primeira vez a imagem é construída e as
dependências são instaladas; depois é rápido.

### A meta de 25%

O playbook do portfólio exige 25% de cobertura no frontend. A meta está no
`frontend/karma.conf.js`, e o comando **falha** abaixo dela, nas quatro medidas
(comandos, linhas, ramos e funções).

### Por que existe o `cobertura.spec.ts`

O Karma só mede o que entra na compilação, e só entra o que algum teste importa.
Sem cuidado, a porcentagem mede apenas os arquivos que já têm teste: a primeira
medição deste projeto deu 72%, mas o total eram 9 arquivos de 35. Com todos
dentro, o número honesto era 27%.

`frontend/src/app/cobertura.spec.ts` importa todos os arquivos do site, para que
o denominador seja o site inteiro. O teste `backend/tests/test_cobertura_frontend.py`
confere que a lista continua completa: arquivo novo que ninguém importar lá
sairia da conta em silêncio.

### O que é testado

| Arquivo | Cobre |
|---|---|
| `core/regras-cliente.spec.ts` | CPF e telefone (RN-C01 e RN-C02) |
| `core/servicos.spec.ts` | Endereço e verbo de cada chamada à API |
| `core/erros.spec.ts` | A trava da assinatura (402) |
| `core/datas.spec.ts` | Conversão de UTC para o horário local |
| `app.component.spec.ts` | Menu e barra lateral |
| `pages/clientes/clientes.component.spec.ts` | Conferência do cadastro antes de chamar a API |
| `pages/configuracoes/cobranca.component.spec.ts` | Salvar e Cancelar, e o envio parcial de campos |

Aparência (cor, espaçamento, tamanho de alvo de toque) não é testada aqui: isso
se mede no navegador, com `getBoundingClientRect()`.
