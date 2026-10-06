# Como conectar seu WhatsApp de verdade

O sistema funciona em **dois modos**:

| Modo | O que acontece | Quando usar |
|---|---|---|
| **Simulador** (padrão) | As mensagens são geradas e registradas no histórico, mas **não são enviadas**. | Para desenvolver, testar e demonstrar sem depender do celular. |
| **Real** (Evolution API) | As mensagens são enviadas de verdade pelo seu número. | Quando quiser usar com clientes reais. |

Hoje o projeto está em **modo simulador**. Tudo funciona, só não sai mensagem.
Para ligar o modo real, siga os passos abaixo.

---

## Passo 1. Escolher uma chave de segurança
Abra o arquivo `.env` e preencha a linha `EVOLUTION_API_KEY` com uma senha
qualquer inventada por você (só serve para o sistema conversar com o WhatsApp):

```
EVOLUTION_API_KEY=uma-chave-secreta-que-voce-inventar
```

> ⚠️ Enquanto essa linha estiver **vazia**, o sistema continua no modo simulador.
> É esse campo que liga o modo real.

## Passo 2. Subir o serviço do WhatsApp
Na pasta do projeto:

```bash
docker compose --profile whatsapp up -d
```

Isso sobe um serviço a mais (a Evolution API), além do banco, da API e da interface.
Na primeira vez ele baixa a imagem, o que leva alguns minutos.

## Passo 3. Criar a instância e escanear o QR Code
1. Abra o sistema em http://localhost:4200 e vá em **Configurações**.
2. O card **WhatsApp** vai mostrar "Não conectado" e exibir um **QR Code**.
3. No celular: abra o **WhatsApp → Configurações → Aparelhos conectados →
   Conectar um aparelho** e escaneie o QR Code da tela.
4. Recarregue a página. O status deve mudar para **Conectado** (bolinha verde).

> Se o QR Code não aparecer, aguarde alguns segundos e recarregue. A Evolution
> API leva um instante para iniciar.

## Passo 4. Testar
No perfil de um cliente, clique em **Cobrar** em uma parcela. A mensagem deve
chegar no WhatsApp do número cadastrado naquele cliente.

---

## Desligar o modo real
- Para desconectar o número: botão **Desconectar** na tela de Configurações.
- Para voltar ao simulador: apague o valor de `EVOLUTION_API_KEY` no `.env` e rode
  `docker compose restart backend`.
- Para parar o serviço: `docker compose --profile whatsapp down`.

---

## Como o sistema se comporta

- **Envio automático**: o agendador varre as parcelas de hora em hora, das **08h
  às 20h** (horário de Brasília), e envia lembrete/vencimento/atraso conforme a
  data. Respeita o limite de **3 mensagens automáticas por cliente por dia**.
- **Respostas do devedor**: o cliente responde **1**, **2** ou **3**. Texto livre é
  ignorado e recebe um aviso automático de que o canal é só para cobranças.
- **"1 - Já paguei" não confirma o pagamento**: a parcela fica como *Aguardando
  confirmação* e **você** decide se marca como paga no sistema.
- **Resumo diário**: enviado ao seu próprio WhatsApp no horário configurado, e
  somente se houve atividade no dia.
- **Se a conexão cair**: as mensagens ficam com status *Na fila* e são reenviadas
  quando a conexão voltar.
