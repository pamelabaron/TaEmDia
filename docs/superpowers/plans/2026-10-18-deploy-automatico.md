# Deploy automático. Plano de implementação

> **Para quem for executar:** use `superpowers:executing-plans`. Os passos usam
> caixas (`- [ ]`) para marcar.

**Objetivo:** enviar o código para o GitHub passa a ser tudo o que é preciso
para o site mudar. Nenhuma etapa por SSH, e a porta 22 pode ser fechada.

**Abordagem:** o GitHub compila as imagens e as guarda; depois pede à AWS que
mande o servidor baixar e trocar. A AWS fala com a máquina por dentro, pelo
agente que já vem instalado no Ubuntu, sem porta aberta. A autenticação entre
GitHub e AWS é por confiança federada (OIDC): nenhuma senha nem chave fica
guardada em lugar nenhum.

**Tecnologias:** GitHub Actions, GitHub Container Registry, AWS Systems
Manager (Run Command), AWS IAM com OIDC.

## Por que assim

O playbook do portfólio veda "deploy via SSH/FTP" e exige "deploy via CI/CD".
As três decisões da autora, tomadas em 18/10/2026:

1. **Pelo serviço da AWS, sem SSH.** Fecha o item do playbook pela raiz, em vez
   de automatizar o que ele proíbe.
2. **Compilar no GitHub.** O servidor tem 909 MB de memória e hoje compila o
   Angular inteiro a cada subida, o que leva de 5 a 10 minutos e usa memória de
   troca em disco. Compilando fora, a subida vira baixar e trocar.
3. **Fechar a porta 22, mas só depois de testar.** Enquanto o caminho novo não
   estiver provado, o caminho velho continua aberto.

## Restrições do projeto

- Nenhum segredo no repositório. Nem chave da AWS, nem senha, nem `.env`.
- A confiança entre GitHub e AWS fica restrita a **este** repositório. Sem
  isso, qualquer repositório do mundo poderia pedir à AWS para mexer na
  máquina.
- O banco e os volumes (`postgres-data`, `uploads-data`) **não** podem ser
  recriados em nenhuma hipótese: são os clientes e os comprovantes.
- O `.env` do servidor permanece onde está e não é tocado pelo deploy.
- Código, comentários e mensagens de commit **em português**.
- **Nunca usar travessão** em texto nenhum.

## Estrutura de arquivos

**Criar:**

- `.github/workflows/deploy.yml` — compila as imagens, guarda no GitHub e pede
  à AWS para trocar.
- `docker-compose.prod.yml` ganha a forma com imagem pronta (ver Tarefa 2).
- `docs/deploy-automatico.md` — o passo a passo dos cliques na AWS, para a
  autora executar e para ficar registrado no TCC.

**Modificar:** `docker-compose.prod.yml`, `docs/deploy.md`,
`backend/tests/test_topologia_producao.py` (a guarda da topologia precisa
conhecer a forma nova).

---

## Tarefa 1: A guarda da topologia aceita imagem pronta

A varredura que confere a produção hoje espera `build:` em cada serviço. Se o
compose mudar antes dela, ela reprova o arquivo certo.

**Arquivos:**
- Modificar: `backend/tests/test_topologia_producao.py`

- [ ] **Passo 1: escrever o teste que falha**

```python
def test_a_api_e_o_agendador_usam_a_mesma_versao(servicos):
    """Imagens diferentes entre os dois significa código diferente rodando,
    e uma cobrança calculada por uma regra e enviada por outra."""
    da_api = servicos["backend"].get("image") or servicos["backend"].get("build")
    do_agendador = servicos["agendador"].get("image") or servicos["agendador"].get("build")
    assert da_api == do_agendador
```

- [ ] **Passo 2: rodar e ver falhar.** Esperado: KeyError ou comparação falsa.
- [ ] **Passo 3: ajustar a varredura para ler `image` além de `build`.**
- [ ] **Passo 4: rodar e ver passar.** **Passo 5: commitar.**

---

## Tarefa 2: O compose de produção usa imagem pronta

**Arquivos:**
- Modificar: `docker-compose.prod.yml`

- [ ] **Passo 1: trocar `build` por `image`, com variável de versão**

```yaml
  backend:
    image: ghcr.io/pamelabaron/taemdia-backend:${VERSAO:-latest}
  agendador:
    image: ghcr.io/pamelabaron/taemdia-backend:${VERSAO:-latest}
  frontend:
    image: ghcr.io/pamelabaron/taemdia-frontend:${VERSAO:-latest}
```

O `:-latest` mantém o comando manual funcionando sem ninguém definir nada.

- [ ] **Passo 2: rodar a varredura da topologia e ver passar.**
- [ ] **Passo 3: commitar.**

---

## Tarefa 3: O robô compila e guarda as imagens

**Arquivos:**
- Criar: `.github/workflows/deploy.yml` (primeira metade)

- [ ] **Passo 1: escrever o trabalho de compilação**

Roda só depois do CI passar, com `workflow_run`. Compila as duas imagens e as
guarda no GitHub Container Registry, marcadas com o identificador do commit.

- [ ] **Passo 2: enviar e conferir que as imagens aparecem no repositório.**
- [ ] **Passo 3: commitar.**

---

## Tarefa 4 (da autora): dar permissão à AWS

São dois cadastros no painel da AWS. O passo a passo com os cliques fica em
`docs/deploy-automatico.md`.

- [ ] **4a. Papel para a máquina.** Um papel com a permissão
  `AmazonSSMManagedInstanceCore`, ligado à instância. É o que deixa a AWS
  conversar com ela por dentro. O agente já está instalado.
- [ ] **4b. Confiança para o GitHub.** Um provedor de identidade apontando
  para o GitHub, e um papel que só aceita pedidos vindos do repositório
  `pamelabaron/TaEmDia`. Sem chave guardada em lugar nenhum.

Conferência: `aws ssm describe-instance-information` precisa listar a máquina.

---

## Tarefa 5: O robô manda trocar a versão

**Arquivos:**
- Modificar: `.github/workflows/deploy.yml` (segunda metade)

- [ ] **Passo 1: autenticar na AWS por OIDC e chamar o Run Command**

O comando que roda na máquina, nesta ordem, e o porquê de cada parte:

```bash
cd /home/ubuntu/TaEmDia
git pull                      # traz compose e configuração do Nginx
export VERSAO=<commit>
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml restart nginx
docker image prune -af --filter "until=72h"
```

O `restart nginx` **não é opcional**: sem ele o site responde 502, porque o
Nginx guarda o endereço interno dos containers de quando subiu. Já aconteceu.

O `prune` existe porque o disco tem 9,4 GB livres e cada subida deixa a imagem
antiga para trás.

- [ ] **Passo 2: esperar o fim do comando e falhar o robô se ele falhar.**

Sem isto o GitHub fica verde enquanto o servidor quebrou.

- [ ] **Passo 3: enviar uma mudança pequena e acompanhar a subida inteira.**
- [ ] **Passo 4: conferir no navegador que a mudança chegou.**
- [ ] **Passo 5: commitar.**

---

## Tarefa 6: Fechar a porta 22

Só depois da Tarefa 5 ter funcionado de ponta a ponta.

- [ ] **Passo 1: provar que dá para entrar na máquina sem SSH**

Pelo painel da AWS, em Session Manager. Se isto não funcionar, **parar aqui** e
deixar a porta aberta: fechar sem caminho de volta é como trancar a chave
dentro de casa.

- [ ] **Passo 2: tirar a regra da porta 22 do grupo de segurança.**
- [ ] **Passo 3: conferir que o site continua no ar e que uma subida funciona.**
- [ ] **Passo 4: atualizar `docs/deploy.md` com o caminho novo de acesso.**

---

## Tarefa 7: Conferência final

- [ ] Uma mudança qualquer enviada ao GitHub chega ao site sozinha
- [ ] O robô fica vermelho quando o servidor falha
- [ ] Um teste quebrado **impede** a subida
- [ ] O site não fica fora do ar durante a troca por mais que alguns segundos
- [ ] O banco e os comprovantes continuam lá
- [ ] `docs/deploy.md` descreve o caminho novo

---

## O que fazer se der errado

O caminho manual continua existindo enquanto a porta 22 estiver aberta:

```bash
ssh -i C:\Users\User\.ssh\taemdia-chave.pem ubuntu@taemdia.duckdns.org
cd TaEmDia && git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml restart nginx
```

A Tarefa 6 só acontece depois que o caminho novo estiver provado, justamente
para que este aqui nunca precise ser usado às pressas.
