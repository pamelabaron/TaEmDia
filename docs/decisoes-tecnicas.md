# Decisões técnicas

O registro das escolhas de engenharia do TáEmDia: o que foi decidido, por quê,
o que foi descartado, e o preço que se paga. Cada item aponta para onde a
decisão vive no código, para poder ser conferida.

Uma decisão sem o preço anotado é propaganda. Por isso todas têm a linha
"O preço".

| # | Decisão | Área |
|---|---|---|
| 1 | [Backend em três camadas](#1-backend-em-três-camadas) | Arquitetura |
| 2 | [Status da parcela calculado, não guardado](#2-status-da-parcela-calculado-não-guardado) | Dados |
| 3 | [Dinheiro em decimal, centavos nas últimas parcelas](#3-dinheiro-em-decimal-centavos-nas-últimas-parcelas) | Dados |
| 4 | [Entrada só pelo Google, sem senha própria](#4-entrada-só-pelo-google-sem-senha-própria) | Segurança |
| 5 | [Identidade vem do token, nunca da requisição](#5-identidade-vem-do-token-nunca-da-requisição) | Segurança |
| 6 | [Ler é sempre liberado; escrever exige assinatura](#6-ler-é-sempre-liberado-escrever-exige-assinatura) | Negócio |
| 7 | [Administradora por variável de ambiente](#7-administradora-por-variável-de-ambiente) | Segurança |
| 8 | [Regras como funções puras, com espelho conferido](#8-regras-como-funções-puras-com-espelho-conferido) | Qualidade |
| 9 | [Validação na tela e na API](#9-validação-na-tela-e-na-api) | Qualidade |
| 10 | [Telefone guardado pronto para envio](#10-telefone-guardado-pronto-para-envio) | Dados |
| 11 | [WhatsApp atrás de um contrato](#11-whatsapp-atrás-de-um-contrato) | Integração |
| 12 | [Uma cobrança por parcela por dia](#12-uma-cobrança-por-parcela-por-dia) | Negócio |
| 13 | [Reenvio que confere antes de mandar](#13-reenvio-que-confere-antes-de-mandar) | Negócio |
| 14 | [Disparo manual fora das regras automáticas](#14-disparo-manual-fora-das-regras-automáticas) | Negócio |
| 15 | [API sob /api](#15-api-sob-api) | Infraestrutura |
| 16 | [Compilar no GitHub, servidor só baixa](#16-compilar-no-github-servidor-só-baixa) | Deploy |
| 17 | [Chave de usuário técnico, e não OIDC](#17-chave-de-usuário-técnico-e-não-oidc) | Deploy |
| 18 | [Nenhum SSH](#18-nenhum-ssh) | Deploy |
| 19 | [SonarQube Cloud, e não instalado](#19-sonarqube-cloud-e-não-instalado) | Qualidade |
| 20 | [Testes que leem configuração](#20-testes-que-leem-configuração) | Qualidade |
| 21 | [Monitor pelo próprio GitHub](#21-monitor-pelo-próprio-github) | Infraestrutura |
| 22 | [Cor só por token, contraste medido](#22-cor-só-por-token-contraste-medido) | Interface |

---

## 1. Backend em três camadas

**Contexto.** Regra de negócio misturada com HTTP e com SQL é difícil de
testar e de mudar.

**Decisão.** `router` (HTTP) → `service` (regras) → `repository` (banco). O
repository é a **única** camada que toca o banco.

**Descartado.** Tudo no router, como em muito exemplo de FastAPI. Menos
arquivos, mas a regra fica presa ao HTTP.

**O preço.** Mais arquivos por módulo, e alguma repetição entre eles.

**Onde.** `backend/app/modules/*/`. Exemplo completo em `clientes/`.

## 2. Status da parcela calculado, não guardado

**Contexto.** "Atrasada" depende da data de hoje. Uma parcela muda de pendente
para atrasada sem nada acontecer no sistema.

**Decisão.** Não existe coluna de status. Ele é calculado na leitura, a partir
das datas de vencimento e de pagamento e do sinal de "aguardando
confirmação" (RN09).

**Descartado.** Coluna `status` atualizada por uma rotina de madrugada. Se a
rotina falhasse uma noite, o sistema mostraria dado errado sem ninguém notar.

**O preço.** Não dá para filtrar por status direto no SQL. Na escala do
sistema (dezenas a centenas de clientes por conta), calcular em memória é
irrelevante.

**Onde.** `backend/app/modules/vendas/service.py`, `calcular_status`.

## 3. Dinheiro em decimal, centavos nas últimas parcelas

**Contexto.** Em ponto flutuante, 0,1 + 0,2 não dá 0,3. E R$ 100,00 em 3 vezes
não divide exato.

**Decisão.** `Numeric(10, 2)` no banco e `Decimal` no código. A divisão trabalha
em centavos inteiros e põe o que sobra nas últimas parcelas: 33,33 + 33,33 +
33,34.

**Descartado.** Arredondar cada parcela, que faz a soma dar 99,99 ou 100,02.

**O preço.** Conversões explícitas entre `float` e `Decimal` nas bordas.

**Onde.** `vendas/service.py`, `_dividir_valor`. Testes em
`test_vendas_calculos.py`.

## 4. Entrada só pelo Google, sem senha própria

**Contexto.** Guardar senha exige hash correto, fluxo de "esqueci a senha",
proteção contra tentativa em massa, e um vazamento afetaria outros sites,
porque as pessoas repetem senha.

**Decisão.** OAuth 2.0 do Google. O sistema guarda e-mail, nome e o endereço da
foto. Nenhuma senha passa por aqui. A sessão é um JWT próprio de 24 horas,
entregue no fragmento da URL (depois do `#`), que não é enviado a servidor
nenhum e não fica em log.

**Descartado.** Senha própria. E refresh token: reentrar custa um clique, e
manter uma lista de tokens revogados não compensa para uso diário.

**O preço.** Quem não tem conta Google não usa. E um token roubado vale até
vencer.

**Onde.** `backend/app/modules/auth/`, `backend/app/core/security.py`.

## 5. Identidade vem do token, nunca da requisição

**Contexto.** O sistema guarda CPF e dívida de terceiros. Uma conta ver a
carteira de outra acabaria com o produto (RNF07).

**Decisão.** O `vendedor_id` sai do token assinado, e todo método de
repository filtra por ele. Não existe parâmetro que o navegador possa trocar
para pedir dado de outra conta.

**Descartado.** Mandar o id da conta na requisição e confiar no frontend.

**O preço.** Todo método de repository recebe o `vendedor_id`, mesmo quando
parece óbvio.

**Onde.** `auth/deps.py`, `get_current_vendedor_id`. Teste em
`test_api_clientes.py`, `TestIsolamentoEntreContas`.

## 6. Ler é sempre liberado; escrever exige assinatura

**Contexto.** A assinatura vence. O que fazer com quem não renovou?

**Decisão.** Leitura sempre liberada. Cadastrar, cobrar e conectar o WhatsApp
exigem assinatura em dia, e a recusa é **402 Pagamento Necessário**.

**Descartado.** Bloquear tudo. Prender o dado da pessoa como refém seria
indefensável, e a LGPD garante acesso aos próprios dados.

**O preço.** Duas dependências diferentes nas rotas, e é preciso lembrar qual
usar em cada uma.

**Onde.** `assinatura/deps.py`, `exigir_assinatura_ativa`.

## 7. Administradora por variável de ambiente

**Decisão.** Quem confere comprovantes está em `ADMIN_EMAILS`, e não numa
coluna do banco.

**Por quê.** Assim não existe bit a inverter: ninguém vira administrador por
gravação no banco, nem por falha de outra parte do sistema.

**O preço.** Trocar a administradora exige mexer na configuração do servidor.

**Onde.** `core/config.py` e `assinatura/deps.py`, `eh_administrador`.

## 8. Regras como funções puras, com espelho conferido

**Contexto.** Teste que precisa de banco e de servidor é lento e frágil.

**Decisão.** Regras de negócio em funções puras, em arquivos `regras.py`. As de
cliente (CPF, telefone) têm um espelho em TypeScript para a tela validar sem ir
à rede.

**O preço.** Duas cópias da mesma regra podem divergir. Por isso existe um
teste que **falha** se Python e TypeScript saírem de sincronia.

**Onde.** `clientes/regras.py`, `frontend/src/app/core/regras-cliente.ts`,
`test_regras_espelhadas.py`.

## 9. Validação na tela e na API

**Decisão.** Os dois, por motivos diferentes. Na tela, para a pessoa ver o erro
na hora. Na API, porque qualquer um chama a API sem passar pela tela.

**O preço.** Duas camadas de validação para manter (ver decisão 8).

**Onde.** `clientes/schemas.py` e `clientes.component.ts`.

## 10. Telefone guardado pronto para envio

**Contexto.** Números foram salvos sem o 55. O WhatsApp exige o código do país:
uma cobrança para "4799..." não chega a ninguém, e nenhum erro aparece.

**Decisão.** O número é guardado com país, DDD e número (RN-C01), e uma
migração acertou os já cadastrados. A tela recebe o número já formatado da
API, para as duas nunca discordarem.

**O preço.** A migração precisou tratar o conflito de dois cadastros com o
mesmo número em formatos diferentes. Ela para e avisa em vez de apagar.

**Onde.** `clientes/regras.py`, migração `b7c4e1f90a32`.

## 11. WhatsApp atrás de um contrato

**Decisão.** Nenhum módulo importa a biblioteca de WhatsApp. Todos falam com o
contrato `WhatsAppClient`, que tem duas implementações: a Evolution API e um
simulador que registra sem enviar.

**Por quê.** Todo o motor de cobrança foi desenvolvido e testado sem um celular
ligado, e trocar de fornecedor é mexer em um arquivo.

**O preço.** O simulador pode esconder diferenças do serviço real.

**Onde.** `backend/app/modules/whatsapp/client.py`.

## 12. Uma cobrança por parcela por dia

**Contexto.** A varredura roda de hora em hora, das 8h às 20h. O único freio
era o limite de 3 mensagens por dia (RN10), e um cliente com uma parcela
atrasada recebia as três. Quem respondia "1 - Já paguei" continuava sendo
cobrado.

**Decisão.** Cada parcela recebe no máximo uma cobrança automática por dia,
contando a manual e a que está na fila. Parcela "aguardando confirmação" não é
cobrada automaticamente.

**O preço.** Uma consulta a mais por varredura. Se a vendedora conferir e não
achar o pagamento, ela cobra na mão (decisão 14).

**Onde.** `cobrancas/repository.py`, `parcelas_cobradas_no_dia` e
`elegiveis`. Testes em `test_cobranca_sem_repeticao.py`.

## 13. Reenvio que confere antes de mandar

**Contexto.** Mensagem que falha por queda de conexão fica na fila (FE01). A
função de reenvio existia e ninguém a chamava.

**Decisão.** A tarefa horária reenvia a fila **antes** da varredura. Antes de
mandar, confere se ainda faz sentido, e descarta a mensagem quando a parcela
foi paga, o cliente disse que pagou, a venda foi cancelada, o envio automático
foi desligado, ou ela é de outro dia (o texto envelheceu, e a varredura manda
uma versão atual). Vai sempre para o número atual do cliente.

**O preço.** Uma situação nova, "Não enviada", na tela de Cobranças.

**Onde.** `cobrancas/service.py`, `reenviar_pendentes`, e `agente/agendador.py`.

## 14. Disparo manual fora das regras automáticas

**Decisão.** O botão "Cobrar" não respeita horário comercial nem limite diário.

**Por quê.** RN10 e RN11 falam de mensagens **automáticas**. O manual é uma
decisão explícita da vendedora, e ela responde por ele.

**Onde.** `cobrancas/service.py`, `disparar_manual`.

## 15. API sob /api

**Contexto.** Telas do site e rotas da API tinham o mesmo nome (`/clientes`,
`/cobrancas`). Atualizar a página devolvia JSON no lugar da tela.

**Decisão.** No Nginx, a API fica sob `/api`, e o prefixo é tirado antes de
chegar ao backend. O login do Google continua na raiz, porque o endereço de
retorno está cadastrado no Google Cloud.

**Onde.** `docker/nginx/taemdia.conf`. Teste em `test_rotas_no_nginx.py`.

## 16. Compilar no GitHub, servidor só baixa

**Contexto.** O servidor tem 909 MB de memória e levava de 5 a 10 minutos para
compilar o Angular, usando disco como memória.

**Decisão.** O GitHub compila as imagens e as guarda no GitHub Container
Registry, marcadas com o código do commit. O servidor só baixa e troca. O
deploy roda sobre o commit que o CI testou, e só se ele passou.

**O preço.** Depende do GitHub estar no ar. Há um caminho de emergência que
compila no servidor.

**Onde.** `.github/workflows/deploy.yml`, `docs/deploy-automatico.md`.

## 17. Chave de usuário técnico, e não OIDC

**Contexto.** O jeito mais seguro de o GitHub falar com a AWS é OIDC, sem
credencial guardada. Nesta conta, criar o provedor exige "ativar recursos
avançados", que a AWS diz ser **irreversível** e que **remove o limite de
gastos** da conta.

**Decisão.** Usuário técnico com chave, cuja permissão só manda comando nesta
única máquina. Não cria recurso, não lê banco, não gasta.

**O preço.** Existe uma credencial guardada, que precisa ser trocada se vazar.

**Onde.** `docs/deploy-automatico.md`.

## 18. Nenhum SSH

**Decisão.** O deploy fala com a máquina pelo Systems Manager da AWS, por
dentro. A porta 22 foi **fechada** depois de o caminho novo ser testado.
Acesso manual é pelo Session Manager, no navegador.

**O preço.** O script roda com `/bin/sh` (dash, não bash) e como outro usuário,
o que já custou dois deploys quebrados. Está anotado.

## 19. SonarQube Cloud, e não instalado

**Decisão.** A análise estática usa o SonarQube Cloud, a cada envio, no CI.

**Descartado.** SonarQube Community Build instalado: pede cerca de 4 GB de
memória, e o servidor tem 909 MB.

**O preço.** O resultado fica num serviço de fora. Duas marcas foram revisadas
e fechadas como falso positivo, com a justificativa escrita.

**Onde.** `docs/analise-estatica.md`.

## 20. Testes que leem configuração

**Contexto.** Os erros que mais custaram estavam fora do código Python: rota
nova sem caminho no Nginx, arquivo de configuração vazio, condição de CI que
nunca era verdadeira.

**Decisão.** Testes que leem o Nginx, o compose, as rotas do Angular, o CI e a
configuração do Sonar, e falham quando eles estão errados. E um teste que
falha se algum desses estiver **pulando em silêncio**.

**O preço.** Testes que dependem de arquivos fora da pasta do backend, montados
no container.

**Onde.** `backend/tests/test_guardas_ativas.py` e os demais `test_*` de guarda.

## 21. Monitor pelo próprio GitHub

**Decisão.** Um fluxo agendado consulta o site a cada 30 minutos e falha, com
aviso por e-mail, se a API, o banco ou a página não responderem. O `/health`
passou a perguntar ao banco.

**Descartado.** Prometheus com Grafana, do RFC: não cabem na máquina. E serviço
externo de monitoramento, que exigiria conta nova.

**O preço.** Não mede lentidão nem olha dentro do servidor.

**Onde.** `.github/workflows/monitor.yml`, `docs/monitoramento.md`.

## 22. Cor só por token, contraste medido

**Decisão.** Nenhuma tela escreve cor fixa: tudo vem de tokens em `styles.scss`.
As cores têm significado fixo (verde pago, laranja atraso, vermelho
inadimplente, cinza pendente). Um teste monta cada tela e **calcula** o
contraste de todo texto.

**Por quê.** Olhar não achou os seis problemas de contraste que o teste achou.

**Onde.** `frontend/src/styles.scss`, `frontend/src/app/tema-escuro.spec.ts`.
