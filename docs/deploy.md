# Deploy em Produção (AWS EC2)

Guia para colocar o TáEmDia no ar em um servidor, com HTTPS.
Corresponde ao Sprint 10 / Marco M4 do RFC.

> **Antes de começar:** este passo envolve criar uma conta na AWS (exige cartão
> de crédito, mesmo no nível gratuito) e registrar um domínio. Esses cadastros
> precisam ser feitos por você. O restante já está preparado no projeto.

---

## Visão geral

Em produção o sistema roda assim:

```
Internet  →  Nginx (HTTPS)  →  ┬→  frontend (Angular compilado)
                               └→  backend (FastAPI)  →  PostgreSQL
                                                      →  Evolution API
```

Só o Nginx fica exposto. Banco e Evolution API ficam na rede interna do Docker,
sem porta pública.

---

## Passo 1 — Criar o servidor

1. Acesse **https://aws.amazon.com** e crie sua conta.
2. No console, vá em **EC2 → Executar instância**.
3. Escolha:
   - **Nome:** `taemdia`
   - **Sistema:** Ubuntu Server 24.04 LTS
   - **Tipo:** `t3.small` (o `t2.micro` do nível gratuito é apertado para
     rodar banco + API + Evolution juntos)
   - **Par de chaves:** crie um novo e **guarde o arquivo `.pem`** — é ele que
     dá acesso ao servidor.
   - **Regras de firewall:** libere as portas **22** (SSH), **80** e **443**.
4. Anote o **IP público** da instância.

## Passo 2 — Apontar o domínio

No painel de onde você registrou o domínio, crie um registro **A** apontando
para o IP público da instância. Exemplo: `taemdia.com.br → 54.x.x.x`.

Aguarde alguns minutos para propagar.

## Passo 3 — Preparar o servidor

Conecte via SSH (no PowerShell do seu computador):

```bash
ssh -i caminho/para/sua-chave.pem ubuntu@SEU_IP
```

Já dentro do servidor, instale o Docker:

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker ubuntu
```

Saia (`exit`) e conecte de novo, para o Docker valer sem `sudo`.

## Passo 4 — Baixar o projeto

```bash
git clone https://github.com/pamelabaron/TaEmDia.git
cd TaEmDia
```

## Passo 5 — Configurar os segredos

```bash
cp .env.example .env
nano .env
```

Preencha, no mínimo:

```
AMBIENTE=producao
POSTGRES_PASSWORD=<uma senha forte>
DATABASE_URL=postgresql+psycopg://taemdia:<a mesma senha>@db:5432/taemdia
JWT_SECRET=<chave aleatória com 32+ caracteres>
WEBHOOK_TOKEN=<outro segredo aleatório>
FRONTEND_URL=https://seu-dominio.com.br
GOOGLE_REDIRECT_URI=https://seu-dominio.com.br/auth/google/callback
GOOGLE_CLIENT_ID=<do Google Cloud>
GOOGLE_CLIENT_SECRET=<do Google Cloud>
```

Para gerar segredos aleatórios:

```bash
openssl rand -hex 32
```

> **Importante:** no Google Cloud, adicione o novo endereço
> `https://seu-dominio.com.br/auth/google/callback` nos *URIs de
> redirecionamento autorizados* (ver `docs/google-oauth-setup.md`).

## Passo 6 — Emitir o certificado HTTPS

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d seu-dominio.com.br
mkdir -p docker/nginx/certs
sudo cp /etc/letsencrypt/live/seu-dominio.com.br/fullchain.pem docker/nginx/certs/
sudo cp /etc/letsencrypt/live/seu-dominio.com.br/privkey.pem  docker/nginx/certs/
sudo chown $USER docker/nginx/certs/*.pem
```

## Passo 7 — Subir o sistema

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

As migrations do banco são aplicadas automaticamente na subida.

Acompanhe:

```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

> Se a configuração estiver insegura, o backend **não sobe** e informa o que
> falta corrigir — é a validação descrita em `docs/checklist-seguranca.md`.

## Passo 8 — Conferir

- Abra `https://seu-dominio.com.br` — deve aparecer a tela de login.
- `https://seu-dominio.com.br/health` deve responder `{"status":"ok"}`.
- Faça login com Google e confira o painel.

## Passo 9 — WhatsApp (opcional)

```bash
docker compose -f docker-compose.prod.yml --profile whatsapp up -d
```

Depois vá em **Configurações** e escaneie o QR Code
(detalhes em `docs/whatsapp-conectar.md`).

---

## Manutenção

**Atualizar o sistema após novas mudanças:**
```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

**Renovar o certificado** (a cada 90 dias):
```bash
sudo certbot renew
sudo cp /etc/letsencrypt/live/seu-dominio.com.br/*.pem docker/nginx/certs/
docker compose -f docker-compose.prod.yml restart nginx
```

**Backup do banco:**
```bash
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U taemdia taemdia > backup-$(date +%F).sql
```

**Ver o que está rodando:**
```bash
docker compose -f docker-compose.prod.yml ps
```

---

## Custos

O `t3.small` fica em torno de US$ 15/mês, mais o domínio (~R$ 40/ano). Para uma
apresentação de TCC, é possível subir o servidor apenas nos dias necessários e
desligá-lo depois (`docker compose down` e parar a instância na AWS), pagando
somente pelas horas usadas.
