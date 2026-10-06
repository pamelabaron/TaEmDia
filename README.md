# TáEmDia. Sistema de Cobrança Automatizada

> Projeto de Portfólio. Engenharia de Software | Católica SC
> Autora: Pâmela Baron | 2026

---

## Sobre o Projeto

O **TáEmDia** é um sistema web voltado para pequenos empreendedores, autônomos e prestadores de serviço que realizam cobranças de forma manual e desorganizada, geralmente pelo WhatsApp. A proposta é automatizar esse processo, centralizando o controle de clientes, compras parceladas e vencimentos em um único painel, com envio automático de cobranças via WhatsApp.

O problema foi identificado a partir de um caso real e validado com pesquisa com potenciais usuários, onde **100% dos respondentes realizam vendas parceladas**, **83,3% cobram manualmente pelo WhatsApp** e **83,3% usariam o sistema proposto**.

---

## Funcionalidades

| Módulo | O que faz | Situação |
|---|---|---|
| **Autenticação** | Login exclusivo via Google OAuth 2.0 + sessão por JWT | ✅ Implementado |
| **Carteira de Clientes** | Cadastro com histórico de compras, pagamentos e saldo devedor | ✅ Implementado |
| **Vendas e Parcelas** | Venda parcelada (1 a 60x) com cálculo automático dos vencimentos | ✅ Implementado |
| **Cobranças Automatizadas** | Envio por WhatsApp conforme a data, além de disparo manual | ✅ Implementado |
| **Agente de Respostas** | Devedor responde 1/2/3; o sistema registra e alerta o vendedor | ✅ Implementado |
| **Resumo Diário** | Consolidação do dia enviada ao WhatsApp do vendedor | ✅ Implementado |
| **Painel Financeiro** | KPIs, gráfico de recebimentos e lista de inadimplentes | ✅ Implementado |
| **Ranking de Pagadores** | Classificação por comportamento de pagamento | ✅ Implementado |
| **Templates de Mensagem** | Modelos personalizáveis com variáveis dinâmicas e prévia | ✅ Implementado |
| **Configurações do Agente** | Antecedência do lembrete, horário do resumo e conexão do WhatsApp | ✅ Implementado |

### Regras de negócio implementadas

- Envio automático apenas em **horário comercial** (08h–20h, horário de Brasília).
- No máximo **3 mensagens automáticas** por cliente por dia.
- A resposta **"1. Já paguei" não confirma o pagamento**: a parcela fica *aguardando confirmação* e somente o vendedor dá a baixa no sistema.
- Canal **unidirecional**: mensagens de texto livre do devedor são ignoradas, com resposta automática padrão.
- **Isolamento total entre contas**: cada vendedor acessa apenas os próprios dados.

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | Angular 17 + TypeScript + Angular Material |
| Backend | Python 3.12 + FastAPI + Pydantic |
| Banco de Dados | PostgreSQL 16 (SQLAlchemy + Alembic) |
| Autenticação | Google OAuth 2.0 + JWT |
| Mensageria | Evolution API (WhatsApp), com modo simulador para desenvolvimento |
| Agendamento | APScheduler |
| Testes | pytest (218 testes, 90% de cobertura) |
| Execução | Docker + Docker Compose |

---

## Estrutura do Projeto

```
taemdia/
├── backend/                     # API em FastAPI (arquitetura em camadas)
│   ├── app/
│   │   ├── core/                # Configuração e segurança (JWT)
│   │   ├── db/                  # Conexão e base dos modelos
│   │   └── modules/             # Um pacote por módulo do domínio
│   │       ├── auth/            # Google OAuth 2.0 + JWT
│   │       ├── clientes/        # Carteira de clientes
│   │       ├── vendas/          # Vendas e parcelas
│   │       ├── cobrancas/       # Motor de cobrança e histórico
│   │       ├── agente/          # Respostas do devedor, resumo e agendador
│   │       ├── whatsapp/        # Cliente WhatsApp isolado por interface
│   │       ├── templates/       # Modelos de mensagem
│   │       ├── relatorios/      # Dashboard e ranking
│   │       └── configuracoes/   # Preferências do agente
│   ├── alembic/                 # Migrations do banco
│   └── tests/                   # Testes automatizados
│
├── frontend/                    # Interface em Angular
│   └── src/app/
│       ├── core/                # Serviços, guard e interceptor
│       └── pages/               # Telas da aplicação
│
├── docs/                        # Documentação técnica
├── docker-compose.yml
└── COMO-RODAR.md                # Instruções de instalação e execução
```

Cada módulo do backend segue o padrão **router → service → repository**, conforme o
diagrama de componentes do RFC: o router trata HTTP, o service concentra as regras de
negócio e o repository é a única camada que acessa o banco.

---

## Como executar

Pré-requisito: **Docker Desktop**. Com ele instalado:

```bash
docker compose up
```

- Interface: http://localhost:4200
- API: http://localhost:8000
- Documentação interativa da API: http://localhost:8000/docs

O passo a passo completo está em **[COMO-RODAR.md](COMO-RODAR.md)**.

---

## Testes

```bash
docker compose exec backend pytest
```

**218 testes** cobrindo **90%** do backend. Acima da meta de 75% definida no RFC.
Detalhes em [docs/testes.md](docs/testes.md).

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [COMO-RODAR.md](COMO-RODAR.md) | Instalação e execução do projeto |
| [docs/modelo-de-dados.md](docs/modelo-de-dados.md) | Modelo de dados completo (tabelas e relações) |
| [docs/testes.md](docs/testes.md) | Estratégia e cobertura de testes |
| [docs/google-oauth-setup.md](docs/google-oauth-setup.md) | Configuração do login com Google |
| [docs/whatsapp-conectar.md](docs/whatsapp-conectar.md) | Conexão do número de WhatsApp |
| [docs/instalacao-ambiente.md](docs/instalacao-ambiente.md) | Preparação do ambiente de desenvolvimento |

---

## KPIs de Sucesso

- Tempo de resposta da API < 500ms em operações comuns
- Redução de ≥ 50% no tempo gasto com cobranças manuais
- Taxa de sucesso no envio automatizado de cobranças > 90%
- Geração automática de relatórios e dashboard funcional
- Identificação e ranking automático de clientes inadimplentes

---

## Contexto e Problema

Microempreendedores e autônomos enfrentam dificuldades reais no controle de cobranças:

- Controle manual via planilhas, fichas físicas ou anotações
- Cobranças individuais pelo WhatsApp, repetitivas e demoradas
- Ausência de histórico consolidado e métricas financeiras
- Dificuldade em cobrar sem parecer insistente (apontada por 50% dos pesquisados)

As soluções existentes no mercado (Asaas, Conta Azul, Bling) são voltadas para cobranças formais ou ERPs completos, não atendendo esse nicho de forma simples e direta.

---

## Fora do Escopo

- Autenticação por e-mail e senha (o acesso é exclusivamente via conta Google)
- Integração com gateways de pagamento, boletos ou Pix automatizado
- Aplicativo nativo para Android ou iOS (a aplicação é web responsiva)
- Múltiplos operadores por conta
- Notificações por e-mail ou SMS

---

## Status do Projeto

Em desenvolvimento. Módulos principais implementados e testados.

---

## Autora

**Pâmela Baron**
Projeto de Portfólio. Engenharia de Software, Católica SC. 2026
