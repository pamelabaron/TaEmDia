# Deploy em Produção (AWS EC2)

Guia para colocar o TáEmDia no ar em um servidor, com HTTPS.
Corresponde ao Sprint 10 / Marco M4 do RFC.

> **Antes de começar:** este passo envolve criar uma conta na AWS, que exige
> cartão de crédito mesmo no nível gratuito. Esse cadastro precisa ser feito por
> você. O restante já está preparado no projeto.

**Escolhas desta instalação:** instância `t3.micro` (gratuita nos 12 primeiros
meses de uma conta nova) e endereço em subdomínio gratuito do DuckDNS, sem custo
de domínio.

---

## Visão geral

Em produção o sistema roda assim:

```
Internet  →  Nginx (HTTPS)  →  ┬→  frontend (Angular compilado)
                               └→  backend (FastAPI)  →  PostgreSQL
                                                      →  Evolution API

                   agendador (processo separado)  →  PostgreSQL
```

Só o Nginx fica exposto. Banco, Evolution API e agendador ficam na rede interna
do Docker, sem porta pública.

**Por que o agendador é um container separado:** a API sobe com dois workers, e
cada worker é um processo. Se o agendador subisse dentro dela, cada processo
criaria o seu, e o mesmo cliente receberia a mesma cobrança duas vezes, furando
o limite diário da RN10. O serviço `agendador` roda com um processo só, e a API
sobe com `AGENDADOR_ATIVO=false`. Há um teste que quebra a suíte se essa
configuração for desfeita (`backend/tests/test_topologia_producao.py`).

---

## Passo 1 — Criar o servidor

1. Acesse **https://aws.amazon.com** e crie sua conta.
2. No console, vá em **EC2 → Executar instância**.
3. Escolha:
   - **Nome:** `taemdia`
   - **Sistema:** Ubuntu Server 24.04 LTS
   - **Tipo:** `t3.micro`
   - **Armazenamento:** aumente para **20 GB** (o padrão de 8 GB fica apertado
     com as imagens do Docker)
   - **Par de chaves:** crie um novo e **guarde o arquivo `.pem`** — é ele que
     dá acesso ao servidor. Não dá para baixar de novo depois.
   - **Regras de firewall:** libere as portas **22** (SSH), **80** e **443**.
4. Anote o **IP público** da instância.

> **Cuidado com o IP:** por padrão o IP muda toda vez que a instância é
> reiniciada. Em **Rede e segurança → IPs elásticos**, aloque um IP elástico e
> associe à instância. Enquanto ele estiver associado a uma instância ligada,
> não há cobrança.

## Passo 2 — Criar o endereço (DuckDNS)

1. Acesse **https://www.duckdns.org** e entre com uma conta Google ou GitHub.
2. Crie um subdomínio, por exemplo `taemdia` → o endereço fica
   `taemdia.duckdns.org`.
3. No campo **current ip**, coloque o IP público da instância e clique em
   **update ip**.

Confira, no seu computador:

```bash
ping taemdia.duckdns.org
```

O IP que responder precisa ser o da instância. Se ainda não for, aguarde alguns
minutos.

## Passo 3 — Preparar o servidor

Conecte via SSH (no PowerShell do seu computador):

```bash
ssh -i caminho/para/sua-chave.pem ubuntu@taemdia.duckdns.org
```

> Se o Windows recusar a chave por "permissões muito abertas", clique com o
> botão direito no arquivo `.pem` → Propriedades → Segurança → Avançadas →
> Desabilitar herança → remova todos os usuários menos o seu.

Já dentro do servidor, instale o Docker:

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker ubuntu
```

Saia (`exit`) e conecte de novo, para o Docker valer sem `sudo`.

### Memória de troca (obrigatório no t3.micro)

O `t3.micro` tem 1 GB de memória, e **compilar o Angular não cabe nisso**: o
build morre sem explicação clara. Estes comandos criam 2 GB de memória de troca
em disco, que o sistema usa quando a memória real acaba:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Confira (a linha `Swap:` deve mostrar 2,0Gi):

```bash
free -h
```

A troca continua valendo depois de reiniciar, por causa da última linha.

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
FRONTEND_URL=https://taemdia.duckdns.org
GOOGLE_REDIRECT_URI=https://taemdia.duckdns.org/auth/google/callback
GOOGLE_CLIENT_ID=<do Google Cloud>
GOOGLE_CLIENT_SECRET=<do Google Cloud>
ADMIN_EMAILS=p.baron@catolicasc.edu.br
PIX_CHAVE=<sua chave Pix>
PIX_NOME=<nome que aparece no Pix>
```

Para gerar segredos aleatórios:

```bash
openssl rand -hex 32
```

Para salvar no `nano`: `Ctrl+O`, `Enter`, `Ctrl+X`.

> **Importante:** no Google Cloud, adicione o novo endereço
> `https://taemdia.duckdns.org/auth/google/callback` nos *URIs de
> redirecionamento autorizados*, e o endereço `https://taemdia.duckdns.org` nas
> *origens JavaScript autorizadas* (ver `docs/google-oauth-setup.md`).

## Passo 6 — Emitir o certificado HTTPS

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d taemdia.duckdns.org
mkdir -p docker/nginx/certs
sudo cp /etc/letsencrypt/live/taemdia.duckdns.org/fullchain.pem docker/nginx/certs/
sudo cp /etc/letsencrypt/live/taemdia.duckdns.org/privkey.pem  docker/nginx/certs/
sudo chown $USER docker/nginx/certs/*.pem
```

O Let's Encrypt emite certificado para endereço do DuckDNS normalmente.

## Passo 7 — Subir o sistema

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

A primeira subida demora: o Angular é compilado no servidor, e no `t3.micro`
isso leva de 10 a 20 minutos usando a memória de troca. É normal parecer travado.

As migrations do banco são aplicadas automaticamente.

Acompanhe:

```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

> Se a configuração estiver insegura, o backend **não sobe** e informa o que
> falta corrigir — é a validação descrita em `docs/checklist-seguranca.md`.

## Passo 8 — Conferir

```bash
docker compose -f docker-compose.prod.yml ps
```

Devem aparecer, no ar: `db`, `backend`, `agendador`, `frontend` e `nginx`.

- `https://taemdia.duckdns.org/health` deve responder `{"status":"ok"}`.
- Abra `https://taemdia.duckdns.org` — deve aparecer a página de apresentação.
- Faça login com Google e confira o painel.
- Confirme que o agendador está vivo:

```bash
docker compose -f docker-compose.prod.yml logs agendador | tail -5
```

Deve aparecer "Agendador em processo dedicado".

## Passo 9 — WhatsApp (opcional)

```bash
docker compose -f docker-compose.prod.yml --profile whatsapp up -d
```

Depois vá em **Configurações** e escaneie o QR Code
(detalhes em `docs/whatsapp-conectar.md`).

> Use um **chip secundário**, nunca seu número pessoal: a Evolution API
> automatiza o WhatsApp por fora da API oficial, e existe risco de bloqueio.

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
sudo cp /etc/letsencrypt/live/taemdia.duckdns.org/*.pem docker/nginx/certs/
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

**Espaço em disco** (as imagens do Docker enchem os 20 GB com o tempo):
```bash
df -h
docker system prune -af   # remove imagens antigas não usadas
```

---

## Custos

O `t3.micro` é gratuito nos 12 primeiros meses de uma conta nova (750 horas por
mês, que cobrem o mês inteiro ligado). O endereço do DuckDNS é gratuito. Fora da
franquia, a instância fica em torno de US$ 7 a 9 por mês.

Para economizar depois da franquia, é possível manter o servidor ligado apenas
nos dias necessários e parar a instância no console da AWS — mas note que, com o
servidor desligado, **as cobranças automáticas não são enviadas**, porque o
agendador depende de um servidor ligado.
