# Deploy automático

Enviar o código para o GitHub é tudo o que é preciso para o site mudar.
Nenhuma etapa por SSH.

## Como funciona

```
você envia o código
        ↓
   o CI roda os testes          ← teste quebrado para aqui
        ↓
   o GitHub compila as imagens
        ↓
   o GitHub pede à AWS
        ↓
   a AWS manda a máquina baixar e trocar
        ↓
   o robô confere se o site respondeu
```

Três coisas valem notar:

- **Teste quebrado não vira site no ar.** O deploy só começa se o CI tiver
  passado, e ele roda sobre o commit que o CI testou, não sobre o topo da
  branch.
- **A compilação acontece no GitHub.** O servidor tem 909 MB de memória e
  levava de 5 a 10 minutos para compilar o Angular, usando memória de troca em
  disco. Agora ele só baixa.
- **Nenhuma senha fica guardada.** A autenticação entre GitHub e AWS é por
  confiança federada (OIDC): a AWS confere quem está pedindo na hora, e aceita
  apenas pedidos vindos deste repositório.

## O que precisa ser feito uma vez, no painel da AWS

São dois cadastros. Depois disto, nunca mais.

Os dados desta instalação:

| | |
|---|---|
| Máquina (instância) | `i-084fdc0991f9456fe` |
| Região | `us-east-2` (Ohio) |
| Repositório | `pamelabaron/TaEmDia` |

### Parte 1. Deixar a AWS falar com a máquina

O agente que faz isso **já está instalado** no Ubuntu. Falta dar permissão.

1. Abra o painel da AWS e procure por **IAM**
2. No menu da esquerda, **Roles** (Funções), e clique em **Create role**
3. Em "Trusted entity type", escolha **AWS service**
4. Em "Use case", escolha **EC2** e clique em **Next**
5. Na busca de permissões, digite `AmazonSSMManagedInstanceCore` e marque a
   caixa dela. Clique em **Next**
6. Em "Role name", escreva `taemdia-maquina` e clique em **Create role**

Agora ligar esse papel à máquina:

7. Vá para **EC2**, **Instances**, e marque a instância `i-084fdc0991f9456fe`
8. Menu **Actions** → **Security** → **Modify IAM role**
9. Escolha `taemdia-maquina` e clique em **Update IAM role**

**Como conferir:** ainda no EC2, com a instância marcada, a aba **Connect**
passa a oferecer **Session Manager**. Se o botão "Connect" dessa aba abrir um
terminal, está funcionando. Pode levar uns dois minutos para aparecer.

### Parte 2. Deixar o GitHub pedir à AWS

1. Em **IAM**, menu da esquerda, **Identity providers**, **Add provider**
2. Escolha **OpenID Connect**
3. Em "Provider URL", cole: `https://token.actions.githubusercontent.com`
4. Clique em **Get thumbprint**
5. Em "Audience", cole: `sts.amazonaws.com`
6. Clique em **Add provider**

Agora o papel que o GitHub vai usar:

7. Em **Roles**, **Create role**
8. Escolha **Web identity**
9. Em "Identity provider", escolha `token.actions.githubusercontent.com`
10. Em "Audience", escolha `sts.amazonaws.com`
11. Em "GitHub organization", escreva `pamelabaron`.
    Em "GitHub repository", escreva `TaEmDia`.
    Em "GitHub branch", escreva `main`
12. **Next**. Na busca de permissões, marque `AmazonSSMFullAccess`
13. Em "Role name", escreva `taemdia-deploy` e clique em **Create role**
14. Abra o papel recém-criado e copie o **ARN** (começa com `arn:aws:iam::`)

> O passo 11 é o que impede qualquer outro repositório do mundo de pedir à AWS
> para mexer na sua máquina. Não pule e não deixe em branco.

### Parte 3. Contar ao GitHub

No GitHub, em **Settings** → **Secrets and variables** → **Actions**, aba
**Secrets**, crie dois:

| Nome | Valor |
|---|---|
| `AWS_PAPEL_DEPLOY` | o ARN que você copiou no passo 14 |
| `AWS_INSTANCIA` | `i-084fdc0991f9456fe` |

## Como subir, daqui em diante

```bash
git push
```

É só. Acompanhe em **Actions**, no fluxo chamado **Deploy**.

Para subir sem enviar código (refazer a última subida, por exemplo): em
**Actions**, escolha **Deploy** e clique em **Run workflow**.

## Se der errado

Enquanto a porta 22 estiver aberta, o caminho manual continua:

```bash
ssh -i C:\Users\User\.ssh\taemdia-chave.pem ubuntu@taemdia.duckdns.org
cd TaEmDia
git pull
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml restart nginx
```

E se as imagens prontas não existirem (GitHub fora do ar, por exemplo), dá
para compilar no próprio servidor:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.build.yml up -d --build
docker compose -f docker-compose.prod.yml restart nginx
```

Esse caminho leva de 5 a 10 minutos e aperta a memória da máquina. É
emergência, não rotina.

## Depois que estiver funcionando

Com o deploy novo provado, a porta 22 pode ser fechada: em **EC2** →
**Security Groups** → o grupo da instância → **Edit inbound rules**, remova a
regra da porta 22.

A partir daí, para entrar na máquina use **Session Manager**, na aba
**Connect** da instância. Sem porta aberta e sem chave para guardar.

**Não feche a porta antes de testar o Session Manager.** Fechar sem o caminho
novo provado é trancar a chave dentro de casa.
