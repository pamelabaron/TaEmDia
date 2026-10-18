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
  passado, e roda sobre o commit que o CI testou, não sobre o topo da branch.
- **A compilação acontece no GitHub.** O servidor tem 909 MB de memória e
  levava de 5 a 10 minutos para compilar o Angular, usando memória de troca em
  disco. Agora ele só baixa, e a troca leva segundos.
- **Nada passa pela porta 22.** A AWS fala com a máquina por dentro, pelo
  agente que já vem instalado no Ubuntu.

## Por que chave de usuário, e não confiança federada

O método mais seguro seria a confiança federada (OIDC): o GitHub prova quem é
na hora e nenhuma credencial fica guardada. Nesta conta ele não foi usado, e o
motivo é concreto.

Criar o provedor de identidade que o OIDC exige está atrás de **"Ativar
recursos avançados"**, e a documentação da AWS diz duas coisas sobre esse
botão: a ativação **não pode ser desfeita**, e ela **remove o limite de gastos
da conta, sem permitir recriá-lo**. Num projeto de faculdade, trocar um teto
de gastos permanente por um método de login não compensa.

A escolha foi usuário técnico com chave, e o risco dela é contido pela
permissão: ela consegue mandar comando **nesta única máquina** e nada mais.
Não cria recurso, não lê banco, não gasta.

## O que precisa ser feito uma vez, no painel da AWS

Dados desta instalação:

| | |
|---|---|
| Máquina (instância) | `i-084fdc0991f9456fe` |
| Região | `us-east-2` (Ohio) |
| Repositório | `pamelabaron/TaEmDia` |

### Parte 1. Deixar a AWS falar com a máquina

**Esta parte já está feita.** A instância tem o papel `taemdia-maquina` com a
permissão `AmazonSSMManagedInstanceCore`, e o agente está registrado.

Como foi feito, para registro: em **IAM** → **Funções** → **Criar função** →
**Serviço da AWS** → **EC2**, com a permissão `AmazonSSMManagedInstanceCore`,
nome `taemdia-maquina`. Depois, em **EC2** → a instância → **Ações** →
**Segurança** → **Modificar função do IAM**.

Efeito colateral útil: a aba **Conectar** da instância passou a oferecer
**Session Manager**, que é entrar na máquina pelo navegador, sem SSH.

### Parte 2. Criar o usuário que o GitHub vai usar

1. Em **IAM**, no menu da esquerda, **Políticas**, botão **Criar política**
2. Escolha a aba **JSON** e cole o texto abaixo, **trocando
   `SEU-NUMERO-DE-CONTA`** pelo número da sua conta (fica no canto superior
   direito do painel, ao clicar no seu nome):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MandarComandoNaMaquinaDoTaEmDia",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": [
        "arn:aws:ec2:us-east-2:SEU-NUMERO-DE-CONTA:instance/i-084fdc0991f9456fe",
        "arn:aws:ssm:us-east-2::document/AWS-RunShellScript"
      ]
    },
    {
      "Sid": "LerOResultadoDoComando",
      "Effect": "Allow",
      "Action": [
        "ssm:GetCommandInvocation",
        "ssm:ListCommandInvocations"
      ],
      "Resource": "*"
    }
  ]
}
```

3. **Próximo**, nome `taemdia-deploy`, **Criar política**

> O primeiro bloco é o que limita tudo: a permissão de mandar comando vale
> **só** para a instância `i-084fdc0991f9456fe`. O segundo bloco é apenas para
> ler a resposta, e não permite ação nenhuma.

Agora o usuário:

4. Em **Usuários do IAM**, **Criar usuário**
5. Nome: `taemdia-deploy`. **Não** marque acesso ao console. **Próximo**
6. Em permissões, escolha **Anexar políticas diretamente**, busque
   `taemdia-deploy` e marque. **Próximo**, **Criar usuário**
7. Abra o usuário criado, aba **Credenciais de segurança**
8. Em "Chaves de acesso", **Criar chave de acesso**
9. Escolha **Aplicação em execução fora da AWS**, confirme, **Próximo**,
   **Criar chave de acesso**
10. Copie os dois valores que aparecem: **ID da chave** e **Chave secreta**

> A chave secreta aparece **uma vez só**. Se fechar a tela sem copiar, apague
> a chave e crie outra.

### Parte 3. Contar ao GitHub

No GitHub, em **Settings** → **Secrets and variables** → **Actions**, aba
**Secrets**, crie três:

| Nome | Valor |
|---|---|
| `AWS_CHAVE_ID` | o ID da chave, do passo 10 |
| `AWS_CHAVE_SECRETA` | a chave secreta, do passo 10 |
| `AWS_INSTANCIA` | `i-084fdc0991f9456fe` |

Depois de colados, o GitHub nunca mais mostra os valores, nem para você. Isso
é proposital.

## Como subir, daqui em diante

```bash
git push
```

É só. Acompanhe em **Actions**, no fluxo chamado **Deploy**.

Para subir sem enviar código: em **Actions**, escolha **Deploy** e clique em
**Run workflow**.

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

## Trocar a chave, se precisar

Se a chave vazar, ou por higiene de tempos em tempos: crie uma chave nova para
o mesmo usuário, troque os dois segredos no GitHub, confirme que uma subida
funciona, e só então apague a chave antiga.

## Depois que estiver funcionando

Com o deploy novo provado, a porta 22 pode ser fechada: em **EC2** →
**Grupos de segurança** → o grupo da instância → **Editar regras de entrada**,
remova a regra da porta 22.

A partir daí, para entrar na máquina use **Session Manager**, na aba
**Conectar** da instância.

**Não feche a porta antes de testar o Session Manager.** Fechar sem o caminho
novo provado é trancar a chave dentro de casa.
