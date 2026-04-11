# TaEmDia - Sistema de Cobrança Automatizada

> Projeto de Portfólio — Engenharia de Software | Católica SC  
> Autora: Pâmela Baron | Versão 1.0 | Abril/2026

---

## Sobre o Projeto

O **TaEmDia** é um sistema web voltado para pequenos empreendedores, autônomos e prestadores de serviço que realizam cobranças de forma manual e desorganizada, geralmente pelo WhatsApp. A proposta é automatizar esse processo, centralizando o controle de clientes, compras parceladas e vencimentos em um único painel, com envio automático de cobranças via WhatsApp.

O problema foi identificado a partir de um caso real e validado com pesquisa com potenciais usuários, onde **100% dos respondentes realizam vendas parceladas**, **83,3% cobram manualmente pelo WhatsApp** e **83,3% usariam o sistema proposto**.

---

## Funcionalidades Previstas

- **Carteira de Clientes** — cadastro completo com histórico de compras e pagamentos
- **Módulo de Cobranças Automatizadas** — disparo de mensagens via WhatsApp baseado em datas de vencimento
- **Painel Financeiro (Dashboard)** — indicadores, valores em aberto e relatórios
- **Ranking de Pagadores** — classificação de bons e maus pagadores por comportamento
- **Configurações do Agente** — personalização de abordagem, mensagens e ativação por cliente
- **Catálogo de Produtos** — envio automático para clientes bons pagadores

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | React |
| Backend | Python |
| Banco de Dados | PostgreSQL |
| Autenticação | JWT |
| Mensageria | WhatsApp API (a definir) |
| Outros | A definir conforme evolução do projeto |

---

## Prototipo de Estrutura Inicial do Projeto (em construção)

```
cobrancazap/
├── backend/                  # API Python
│   ├── app/
│   │   ├── models/           # Modelos do banco de dados
│   │   ├── routes/           # Endpoints da API
│   │   ├── services/         # Regras de negócio
│   │   └── utils/            # Helpers e utilitários
│   ├── requirements.txt
│   └── main.py
│
├── frontend/                 # Interface React
│   ├── src/
│   │   ├── components/       # Componentes reutilizáveis
│   │   ├── pages/            # Páginas da aplicação
│   │   ├── services/         # Chamadas à API
│   │   └── context/          # Contextos (auth, tema, etc.)
│   └── package.json
│
├── docs/                     # Documentação do projeto
│   └── RFC_n1.pdf
│
└── README.md
```

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

## Status do Projeto

Em desenvolvimento — fase de proposta e planejamento (RFC v1.0)

---

##  Autora

**Pâmela Baron**  
Projeto de Portfólio — 2026
