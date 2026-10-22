# Documentos legais

O sistema guarda nome, CPF, telefone e endereço de **terceiros**: pessoas que
devem ao vendedor, que nunca entraram no site e que talvez nem saibam que
estão cadastradas. Isso coloca o projeto dentro da LGPD (Lei 13.709/2018), e
não como formalidade: são dados pessoais sensíveis de gente que não deu
consentimento direto a este sistema.

## Onde estão

| Documento | Endereço |
|---|---|
| Política de Privacidade | https://taemdia.duckdns.org/privacidade |
| Termos de Uso | https://taemdia.duckdns.org/termos |

O texto vive nos próprios componentes das páginas
(`frontend/src/app/pages/legal/`), em um lugar só. Manter uma cópia aqui
criaria duas versões do mesmo texto jurídico, e uma delas envelheceria.

As duas páginas são **abertas**, sem exigir login. É deliberado: quem mais
precisa lê-las é justamente quem ainda não tem conta, e o cliente do vendedor,
que foi cadastrado por outra pessoa.

## A decisão que estrutura os dois documentos

A LGPD separa dois papéis:

- **Controlador**: quem decide usar o dado e para quê
- **Operador**: quem apenas executa o tratamento a pedido do controlador

No TáEmDia os dois existem ao mesmo tempo, em dados diferentes:

| Dado | Controlador | Operador |
|---|---|---|
| Nome, e-mail e foto do vendedor | TáEmDia | (ele mesmo) |
| Nome, CPF, telefone do cliente | **O vendedor** | TáEmDia |

O vendedor obteve o CPF e o telefone na relação comercial dele, e decidiu
cadastrá-los. O TáEmDia nunca pediu esses dados a ninguém: ele guarda e
processa a pedido do vendedor.

Misturar os papéis seria errado nos dois sentidos. A autora responderia por um
CPF que nunca pediu, e o vendedor ficaria sem a responsabilidade que é dele
sobre dados que ele próprio coletou.

## Terceiros envolvidos

| Serviço | Para quê | O que recebe |
|---|---|---|
| Google | Entrada no sistema | Pedido de autenticação; devolve nome, e-mail e foto |
| Amazon Web Services | Onde o sistema roda | Todos os dados armazenados |
| WhatsApp | Envio das cobranças | Número do destinatário e o texto da mensagem |

## O que os testes protegem

`backend/tests/test_documentos_legais.py` reprova três descuidos fáceis:

1. **As páginas atrás de login.** Bastaria alguém acrescentar o `authGuard`
   por hábito, e o documento deixaria de cumprir a função.
2. **O link sumir do rodapé.** Documento publicado que ninguém acha é o mesmo
   que documento inexistente.
3. **O contato virar texto de exemplo.** Prometer um canal que não existe é
   pior do que não prometer nada.

## Limites

Os textos foram escritos com base na LGPD e no Código de Defesa do Consumidor,
mas **não passaram por revisão de advogado**. Para um projeto acadêmico em
operação, cumprem a função. Antes de operação comercial de verdade, valeria
uma revisão profissional.
