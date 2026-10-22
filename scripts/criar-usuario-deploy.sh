#!/usr/bin/env bash
# Cria, de uma vez, o usuário que o GitHub usa para mandar o deploy.
#
# Onde rodar: no CloudShell da AWS, que é o terminal dentro do próprio painel.
# Ele já entra autenticado como você, então não precisa configurar nada nem
# digitar senha. Procure o ícone de terminal (>_) no topo do painel da AWS.
#
# O que ele cria:
#   - a política taemdia-deploy, que permite mandar comando em UMA máquina;
#   - o usuário taemdia-deploy, sem acesso ao painel;
#   - uma chave de acesso para esse usuário.
#
# Rodar duas vezes não estraga nada: ele avisa o que já existe e segue.
set -uo pipefail

INSTANCIA="i-084fdc0991f9456fe"
REGIAO="us-east-2"
NOME="taemdia-deploy"

echo "==> Descobrindo o número da conta"
CONTA=$(aws sts get-caller-identity --query Account --output text) || {
  echo "Não consegui falar com a AWS. Você está no CloudShell?"; exit 1;
}
echo "    conta: $CONTA"

echo "==> Criando a política de permissão"
cat > /tmp/politica.json <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MandarComandoNaMaquinaDoTaEmDia",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": [
        "arn:aws:ec2:${REGIAO}:${CONTA}:instance/${INSTANCIA}",
        "arn:aws:ssm:${REGIAO}::document/AWS-RunShellScript"
      ]
    },
    {
      "Sid": "LerOResultadoDoComando",
      "Effect": "Allow",
      "Action": ["ssm:GetCommandInvocation", "ssm:ListCommandInvocations"],
      "Resource": "*"
    }
  ]
}
JSON

POLITICA="arn:aws:iam::${CONTA}:policy/${NOME}"
if aws iam get-policy --policy-arn "$POLITICA" >/dev/null 2>&1; then
  echo "    já existia, seguindo"
else
  aws iam create-policy \
    --policy-name "$NOME" \
    --policy-document file:///tmp/politica.json \
    --description "Deixa o GitHub mandar o deploy na maquina do TaEmDia" \
    >/dev/null && echo "    criada"
fi

echo "==> Criando o usuário"
if aws iam get-user --user-name "$NOME" >/dev/null 2>&1; then
  echo "    já existia, seguindo"
else
  aws iam create-user --user-name "$NOME" >/dev/null && echo "    criado"
fi

echo "==> Ligando a permissão ao usuário"
aws iam attach-user-policy --user-name "$NOME" --policy-arn "$POLITICA" \
  && echo "    pronto"

echo "==> Conferindo se já existe chave antiga"
ANTIGAS=$(aws iam list-access-keys --user-name "$NOME" \
  --query "AccessKeyMetadata[].AccessKeyId" --output text)
if [ -n "$ANTIGAS" ]; then
  echo
  echo "    ATENÇÃO: este usuário já tem chave ($ANTIGAS)."
  echo "    A AWS permite no máximo duas. Se você perdeu a anterior, apague-a:"
  echo "      aws iam delete-access-key --user-name $NOME --access-key-id $ANTIGAS"
  echo "    e rode este script de novo."
  echo
fi

echo "==> Gerando a chave de acesso"
CHAVE=$(aws iam create-access-key --user-name "$NOME" \
  --query "AccessKey.[AccessKeyId,SecretAccessKey]" --output text) || {
  echo "Não consegui criar a chave. Veja o aviso acima sobre chave antiga."; exit 1;
}

ID=$(echo "$CHAVE" | cut -f1)
SEGREDO=$(echo "$CHAVE" | cut -f2)

cat <<FIM

========================================================================
PRONTO. Agora copie estes dois valores para o GitHub.

  AWS_CHAVE_ID
  $ID

  AWS_CHAVE_SECRETA
  $SEGREDO

No seu computador, rode os dois comandos abaixo, um de cada vez. Cada um
vai pedir o valor: cole e dê Enter. O valor não aparece na tela.

  gh secret set AWS_CHAVE_ID
  gh secret set AWS_CHAVE_SECRETA

Ou cole pelo site:
  https://github.com/pamelabaron/TaEmDia/settings/secrets/actions

A chave secreta não pode ser recuperada depois. Se perder, apague esta
chave e rode o script de novo.

Depois de copiar, feche esta janela do CloudShell.
========================================================================
FIM
