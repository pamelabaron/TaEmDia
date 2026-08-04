# TáEmDia

Sistema web de **cobrança automatizada via WhatsApp** e **gestão de carteira de clientes**,
voltado a pequenos empreendedores. Projeto de portfólio / TCC — Engenharia de Software, Católica SC.
Autora: **Pámela Baron**.

Documento base do projeto: RFC v1.0. Modelo de dados: [`docs/modelo-de-dados.md`](docs/modelo-de-dados.md).

---

## O que este sistema faz (resumo)
- Cadastro de clientes e vendas parceladas, com cálculo automático de vencimentos.
- Envio automático de cobranças pelo WhatsApp, com respostas numeradas (1/2/3) do devedor.
- Confirmação manual de pagamento pelo vendedor, ranking de pagadores e resumo diário no WhatsApp.
- Dashboard financeiro com KPIs e relatórios em PDF.

## Tecnologias
| Camada        | Tecnologia                                             |
|---------------|--------------------------------------------------------|
| Frontend      | Angular 17 + TypeScript + Angular Material             |
| Backend (API) | Python + FastAPI                                       |
| Banco         | PostgreSQL (SQLAlchemy + Alembic)                      |
| Autenticação  | Google OAuth 2.0 + JWT                                 |
| WhatsApp      | Evolution API (self-hosted, a partir do Sprint 5)      |
| Execução      | Docker (tudo roda com um comando)                      |

---

## Como rodar o projeto (passo a passo)

> Você **não precisa** instalar Python, Node ou PostgreSQL separadamente.
> O Docker cuida de tudo. Você só instala **uma** ferramenta: o Docker Desktop.

### 1. Instalar o Docker Desktop (uma vez só)
1. Acesse **https://www.docker.com/products/docker-desktop/** e baixe o instalador para Windows.
2. Execute o instalador e siga o assistente (aceite as opções padrão, incluindo **WSL 2**).
3. Reinicie o computador se for solicitado.
4. Abra o **Docker Desktop** e espere aparecer "Engine running" (baleia verde no canto).

### 2. Preparar as variáveis de ambiente (uma vez só)
1. Copie o arquivo `.env.example` e renomeie a cópia para `.env`.
2. Abra o `.env` e troque as senhas/segredos pelos seus valores.
   (No Sprint 0 os valores padrão já bastam para rodar localmente.)

### 3. Ligar o sistema
Na pasta do projeto, rode:
```bash
docker compose up
```
Isso sobe três serviços juntos (banco, API e interface):
- A **interface (site)** em: http://localhost:4200
- A **API** em: http://localhost:8000
- A **documentação interativa da API** em: http://localhost:8000/docs
- Teste rápido de saúde: http://localhost:8000/health

> A interface (Angular) leva ~30s para compilar na primeira vez. Se abrir
> http://localhost:4200 e ainda não carregar, aguarde alguns segundos e recarregue.

Para desligar, aperte `Ctrl+C` no terminal (ou `docker compose down`).

> **Login:** a tela inicial pede "Continuar com Google". Para o login funcionar,
> configure as credenciais do Google seguindo [`docs/google-oauth-setup.md`](docs/google-oauth-setup.md).

---

## Estrutura do projeto
```
taemdia/
├── backend/          API em FastAPI (arquitetura em camadas)
│   └── app/
│       ├── core/         configurações
│       ├── db/           conexão com o banco
│       └── modules/      um pacote por módulo do domínio
│           └── clientes/   router · service · repository · models · schemas
├── frontend/         Interface em Angular (gerada no Sprint 0)
├── docker/           arquivos auxiliares de container
├── docs/             modelo de dados, requisitos e decisões
├── docker-compose.yml
└── .env.example
```

### Como cada módulo do backend é organizado
O código segue o padrão do RFC (Seção 5.3), em quatro camadas:
- **router** — recebe as requisições da web e devolve as respostas (HTTP).
- **service** — regras de negócio (o "cérebro").
- **repository** — única parte que conversa com o banco de dados.
- **models / schemas** — formato das tabelas e dos dados que entram/saem.

O módulo `clientes` já está pronto como **modelo** para os próximos.

---

## Roadmap (marcos do RFC)
- **M1 – Fundação** (Jul/2026): ambiente, login Google, CRUD de clientes.
- **M2 – MVP** (Ago/2026): vendas, parcelas, cobrança automática, dashboard.
- **M3 – Agente** (Set/2026): respostas do devedor, resumo diário, ranking.
- **M4 – Entrega** (Out–Nov/2026): testes, deploy em produção, documentação.
