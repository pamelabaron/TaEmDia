# Checklist de Segurança Pré-Deploy

Critério do Marco M4 do RFC. Cada item foi verificado no código; os itens
marcados com 🔒 são validados **automaticamente** pela aplicação ao subir em
produção (`AMBIENTE=producao`), que se recusa a iniciar se algo estiver inseguro.

## Autenticação e sessão

| # | Item | Situação |
|---|---|---|
| 1 | Acesso somente via Google OAuth 2.0; nenhuma senha é armazenada | ✅ |
| 2 | Todas as rotas de dados exigem JWT válido | ✅ testado |
| 3 | Token expirado, adulterado ou assinado com outra chave é recusado | ✅ testado |
| 4 | 🔒 `JWT_SECRET` próprio, com 32+ caracteres (não o valor de exemplo) | ✅ validado |
| 5 | Sessão expira automaticamente (24 h por padrão) | ✅ |

## Isolamento de dados (multi-conta)

| # | Item | Situação |
|---|---|---|
| 6 | Toda consulta filtra por `vendedor_id` | ✅ |
| 7 | Um vendedor não lê dados de outro (clientes, vendas, cobranças, relatórios) | ✅ testado |
| 8 | Um vendedor não edita nem cobra parcelas de outro | ✅ testado |
| 9 | O mesmo número de WhatsApp pode existir em contas diferentes, sem vazamento | ✅ testado |

## Webhook do WhatsApp

| # | Item | Situação |
|---|---|---|
| 10 | O webhook exige segredo compartilhado (cabeçalho ou parâmetro) | ✅ testado |
| 11 | Comparação do segredo em tempo constante | ✅ |
| 12 | 🔒 Em produção sem `WEBHOOK_TOKEN`, o webhook fica **desabilitado** | ✅ validado |
| 13 | Respostas duplicadas do devedor são ignoradas | ✅ testado |
| 14 | Texto livre não executa nenhuma ação no sistema | ✅ testado |

## Entrada de dados

| # | Item | Situação |
|---|---|---|
| 15 | Validação de tipos e faixas em toda a API (Pydantic) | ✅ testado |
| 16 | Consultas parametrizadas via ORM — sem concatenação de SQL | ✅ |
| 17 | Conteúdo do usuário é escapado no relatório PDF | ✅ testado |
| 18 | Limite de tamanho de requisição no Nginx (5 MB) | ✅ |

## Rede e transporte

| # | Item | Situação |
|---|---|---|
| 19 | 🔒 HTTPS obrigatório em produção (`FRONTEND_URL` deve ser https) | ✅ validado |
| 20 | HTTP redireciona para HTTPS; TLS 1.2+ | ✅ Nginx |
| 21 | Cabeçalhos HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy | ✅ Nginx |
| 22 | CORS restrito às origens configuradas (sem `*`) | ✅ testado |
| 23 | Banco de dados **sem porta publicada** em produção | ✅ |
| 24 | Evolution API **sem porta publicada** em produção (rede interna) | ✅ |

## Segredos e configuração

| # | Item | Situação |
|---|---|---|
| 25 | `.env` fora do controle de versão | ✅ |
| 26 | Certificados TLS fora do controle de versão | ✅ |
| 27 | 🔒 Senha padrão do banco não pode ir para produção | ✅ validado |
| 28 | 🔒 Credenciais do Google configuradas | ✅ validado |
| 29 | Nenhum segredo em código-fonte ou em log | ✅ |

## Dados pessoais (LGPD)

| # | Item | Situação |
|---|---|---|
| 30 | Coleta mínima: nome e WhatsApp; CPF e endereço são opcionais | ✅ |
| 31 | Exclusão de cliente é desativação, preservando o histórico financeiro | ✅ testado |
| 32 | Base legal e finalidade de cada dado documentadas no RFC (seção 6.3) | ✅ |

---

## Como verificar

A validação de produção pode ser conferida a qualquer momento:

```bash
docker compose exec backend python -c "from app.core.config import Settings; s = Settings(AMBIENTE='producao'); print(s.validar_para_producao() or 'Configuracao pronta para producao')"
```

Se aparecer uma lista, são os pontos que ainda precisam ser corrigidos antes do
deploy. Se aparecer "Configuracao pronta para producao", o checklist automático
está satisfeito.

Os controles acima também são cobertos por testes automatizados
(`backend/tests/test_seguranca.py` e `test_fluxo_completo.py`).
