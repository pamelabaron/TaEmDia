# Guia para a prova de autoria. TáEmDia

Este é o seu material de estudo, não documentação do projeto. Ele existe para
que você consiga responder ao professor **abrindo o seu próprio código**, sem
depender de busca, de anotação ou de ninguém.

Tudo o que está aqui foi conferido no repositório em 27 de outubro de 2026. Os
três ensaios da Parte 5 foram **executados de verdade** antes de serem escritos,
e o resultado que eles prometem é o resultado que saiu.

---

## Como usar este guia

Você tem até 30 de novembro. A prova é individual, oral, e o professor pode
pedir mudanças no código na hora.

**Plano de quatro etapas.** Não tente decorar. Entenda a Parte 2 e o resto cola.

| Etapa | O que fazer | Tempo |
|---|---|---|
| 1 | Ler as Partes 1 e 2 até conseguir desenhar o diagrama de memória | 2 horas |
| 2 | Percorrer as 25 perguntas da Parte 4 **com o código aberto na tela** | 4 horas, em 2 dias |
| 3 | Fazer os três ensaios da Parte 5 sozinha, do zero, cronometrando | 2 horas |
| 4 | Repetir a Parte 5 na véspera, e reler a Parte 6 | 1 hora |

**A regra que mais vale.** Quando ele perguntar, não comece a falar. Abra o
arquivo primeiro, depois fale olhando para ele. Quem sabe onde a coisa está
demonstra domínio mesmo quando erra um detalhe. Quem recita de cor e não acha o
arquivo demonstra o contrário.

---

## Parte 1. O sistema em dez minutos

### O que o TáEmDia faz

Um vendedor pequeno (uma sacoleira, uma loja de bairro) vende parcelado e
anota em caderno. Ele esquece de cobrar, perde o controle de quem deve o quê, e
fica sem jeito de pedir.

O TáEmDia resolve isso em três movimentos:

1. Ele **cadastra** o cliente e a venda parcelada. O sistema calcula sozinho os
   valores e as datas de cada parcela.
2. Ele **cobra** pelo WhatsApp, sozinho, na data certa, com um texto que o
   vendedor escreveu antes.
3. Ele **acompanha**: quem pagou, quem atrasou, quanto cada um deve, e manda um
   resumo do dia no fim da tarde.

Quem recebe a cobrança é o cliente do vendedor. Essa pessoa **nunca entra no
sistema**. Isso tem consequência legal, e é o motivo de existirem a Política de
Privacidade e os Termos.

### O desenho que você precisa saber fazer de cabeça

Decore este caminho. É a primeira pergunta da prova.

```
   A PESSOA no navegador
           |
           |  (1) clica em "Cadastrar cliente"
           v
   ANGULAR, a interface            frontend/src/app/pages/clientes/clientes.component.ts
           |
           |  (2) chama o servico de dados
           v
   ClientesService                 frontend/src/app/core/clientes.service.ts
           |
           |  (3) o interceptor carimba o cracha (token) na requisicao
           v
   authInterceptor                 frontend/src/app/core/auth.interceptor.ts
           |
           |  (4) sai pela rede: POST /api/clientes
           v
   NGINX, o porteiro               docker/nginx/taemdia.conf
           |                       (so em producao; em casa a chamada vai direta)
           |  (5) tira o "/api" e repassa
           v
   ROUTER, a porta da API          backend/app/modules/clientes/router.py
           |
           |  (6) confere o cracha e a assinatura antes de deixar passar
           |      auth/deps.py  +  assinatura/deps.py
           v
   SCHEMA, o conferente            backend/app/modules/clientes/schemas.py
           |                       (CPF valido? telefone com DDD? nome no tamanho?)
           |  (7) dados aprovados
           v
   SERVICE, as regras              backend/app/modules/clientes/service.py
           |                       (ja existe esse numero nesta conta?)
           |  (8) manda gravar
           v
   REPOSITORY, o unico que         backend/app/modules/clientes/repository.py
   fala com o banco                (TODA consulta filtra por vendedor_id)
           |
           v
   POSTGRESQL, o banco
```

E a resposta volta pelo mesmo caminho ao contrário.

### Por que em camadas

Se o professor perguntar "por que não fazer tudo num arquivo só", a resposta é
curta e verdadeira:

> Porque cada camada tem um motivo para mudar, e só um. Se amanhã eu trocar o
> banco, mexo só no repository. Se mudar a regra de duplicidade, mexo só no
> service. Se a API virar outra coisa, mexo só no router. Além disso, o
> isolamento entre contas fica garantido em **um lugar só**: como o repository é
> a única camada que toca o banco, basta conferir que todo método dele filtra
> por `vendedor_id`.

### Os números do projeto

| | |
|---|---|
| Commits | 70 |
| Tabelas no banco | 10 |
| Migrações | 10 |
| Testes do backend | 492, cobertura **91%** (meta do playbook: 75%) |
| Testes do frontend | 178, cobertura **66,2%** (meta do playbook: 25%) |
| Telas | 15 rotas |

---

## Parte 2. Vocabulário mínimo

Estes termos vão aparecer. Se você souber estes, entende qualquer pergunta.

**Backend.** A parte que roda no servidor, que ninguém vê. Guarda os dados, faz
as contas, decide o que pode e o que não pode. O nosso é em Python, com FastAPI.

**Frontend.** A parte que roda no navegador da pessoa, as telas. O nosso é em
Angular.

**API.** O cardápio de serviços que o backend oferece. Cada item é um endereço
(`/clientes`, `/vendas`). O frontend "pede do cardápio" pela rede.

**Endpoint ou rota.** Um item do cardápio. `POST /clientes` é "cadastrar um
cliente". `GET /clientes` é "me liste os clientes".

**ORM (SQLAlchemy).** Tradutor entre objetos Python e tabelas do banco. Em vez
de escrever SQL na mão, você escreve `Cliente(nome="Ana")` e ele gera o SQL.
Vantagem: menos erro e **nenhuma brecha de SQL injection**, porque ele nunca cola
texto do usuário dentro do comando.

**Migração (Alembic).** Um arquivo que descreve uma mudança no banco ("criar a
coluna X"). O banco não muda sozinho quando você muda o código: a migração é a
ordem de serviço, e ela fica versionada no Git como o resto.

**Schema (Pydantic).** O conferente na entrada e na saída da API. Define o
formato esperado e **recusa** o que estiver fora. É onde moram os limites de
tamanho e a validação de CPF.

**JWT (JSON Web Token).** O crachá. Depois do login, o servidor emite um texto
assinado que diz "esta pessoa é o vendedor tal, e isso vale até tal hora". O
navegador guarda e apresenta em toda chamada. Como é assinado, não dá para
falsificar sem a chave secreta do servidor.

**OAuth (login com o Google).** Em vez de o TáEmDia guardar senha, ele manda a
pessoa para o Google, o Google confirma quem ela é, e devolve. **Nenhuma senha
passa pelo nosso sistema.** É menos código e menos risco.

**Guard.** Porteiro de tela, no frontend. Impede abrir uma página sem estar
logado.

**Interceptor.** Posto no caminho de toda chamada HTTP do frontend. O nosso
carimba o token na saída e trata 401 e 402 na volta.

**Docker.** Empacota cada serviço (banco, API, site) com tudo de que precisa,
para rodar igual em qualquer máquina. É por isso que o setup é um comando só.

**CI (Integração Contínua).** O robô do GitHub que roda os testes a cada envio
de código.

**Cobertura de testes.** Percentual das linhas do sistema que os testes
executam. 91% significa que, de cada 100 linhas, 91 foram percorridas por algum
teste.

---

## Parte 3. As três decisões que você mais vai ter que defender

### 1. Por que login com o Google, e não senha própria

> Porque senha é o que mais dá problema e o que eu menos quero guardar.
> Guardar senha exige criptografar direito, exige fluxo de "esqueci a senha",
> exige proteger contra tentativa em massa, e ainda assim um vazamento meu
> viraria problema do usuário em outros sites, porque as pessoas repetem senha.
> Com o Google, **o sistema nunca vê senha nenhuma**. O que eu guardo é só o
> e-mail, o nome e o endereço da foto.
>
> O preço: quem não tem conta Google não usa. Para o público do projeto, que é
> vendedor pequeno com celular Android, isso é praticamente ninguém.

### 2. Por que o status da parcela não é guardado no banco

Esta é a decisão de engenharia mais interessante do projeto. Saiba explicar.

> Uma parcela pode estar pendente, atrasada, aguardando conferência ou paga. A
> saída óbvia seria uma coluna `status`. Eu não fiz isso.
>
> O motivo: "atrasada" **depende da data de hoje**. Uma parcela que vence
> amanhã está pendente hoje e atrasada depois de amanhã, e nada aconteceu no
> sistema nesse meio tempo. Com coluna, eu precisaria de uma rotina varrendo o
> banco toda madrugada para atualizar. Se essa rotina falhasse numa noite, o
> sistema mostraria dado errado e ninguém perceberia.
>
> Então o status é **calculado na hora da leitura**, a partir das datas. Está em
> `backend/app/modules/vendas/service.py`, função `calcular_status`, linha 52. São
> nove linhas e não têm como ficar desatualizadas.
>
> O preço: não dá para filtrar por status direto no SQL. Para o tamanho de
> carteira deste sistema (dezenas a centenas de clientes por vendedor), calcular
> em memória é irrelevante.

### 3. Por que `vendedor_id` em toda consulta

> É o requisito RNF07, e eu tratei como requisito de segurança, não como
> detalhe. Se um vendedor conseguir ver a carteira de outro, o sistema inteiro
> perde o sentido, porque o dado que ele guarda é CPF e dívida de terceiros.
>
> A garantia é estrutural: **só o repository toca o banco**, e todo método dele
> recebe `vendedor_id` e filtra por ele. Não existe caminho que pule essa
> camada. E `vendedor_id` não vem do que o navegador mandou: vem **do token
> assinado**, em `backend/app/modules/auth/deps.py`, linha 13. Ou seja, nem
> alterando a requisição na mão dá para pedir dado de outra conta.
>
> Isso tem teste: `backend/tests/test_api_clientes.py`, classe
> `TestIsolamentoEntreContas`, linha 111.

---

## Parte 4. As 25 perguntas, uma a uma

Para cada uma: **o arquivo para abrir**, o que dizer, e o aprofundamento provável.

---

### Arquitetura e decisões

#### 1. Desenhe a arquitetura. Por onde passa uma requisição?

**Abra:** o diagrama da Parte 1 deste guia está na sua cabeça. Desenhe no papel.

Percorra as oito etapas do desenho em voz alta. Depois mostre na tela, nesta
ordem, que cada caixa existe mesmo:

1. `frontend/src/app/pages/clientes/clientes.component.ts` (a tela)
2. `frontend/src/app/core/clientes.service.ts` (a chamada)
3. `frontend/src/app/core/auth.interceptor.ts:26` (o token sendo carimbado)
4. `backend/app/modules/clientes/router.py:33` (a porta de entrada)
5. `backend/app/modules/clientes/service.py:24` (a regra)
6. `backend/app/modules/clientes/repository.py:33` (o banco)

**Se ele aprofundar:** "por que o frontend não fala direto com o banco?" Porque
o navegador está na máquina da pessoa e qualquer um pode abrir e mexer. A senha
do banco estaria à vista, e nenhuma regra seria garantida. O backend é a única
parte em que eu confio, porque é a única que o usuário não controla.

---

#### 2. Por que essa stack? O que foi descartado?

**Diga, nesta ordem:**

| Escolha | Por quê | O que descartei |
|---|---|---|
| **Python + FastAPI** | É a linguagem que eu domino melhor, e o FastAPI gera a documentação da API sozinho (está em `/docs`) e valida os dados de entrada com o Pydantic, sem eu escrever validação na mão | Django, que traz muita coisa pronta que eu não ia usar (painel administrativo, sistema de usuários próprio, templates) e me deixaria com um sistema que eu entendo menos. Node, que eu domino menos |
| **PostgreSQL** | Dado financeiro precisa de transação confiável e de tipo numérico exato. Uso `Numeric(10,2)` para dinheiro, nunca ponto flutuante, porque 0,1 + 0,2 em ponto flutuante não dá 0,3 | SQLite, que não aguenta escrita concorrente e não seria honesto num sistema em produção. MongoDB, porque meus dados são fortemente relacionais (venda tem parcelas, cliente tem vendas) |
| **Angular** | É um framework completo: roteamento, formulários e injeção de dependência já vêm juntos e combinados. Num projeto sozinha, não ter que escolher dez bibliotecas e fazê-las conversar é tempo ganho. E o TypeScript avisa erro de tipo antes de rodar | React, que é mais popular, mas em que cada decisão (rotas, estado, formulários) é uma biblioteca separada |
| **Docker** | O setup inteiro é `docker compose up`. Isso importa porque o avaliador precisa rodar na máquina dele | Instalar Python, Node e Postgres na mão, que é onde projeto de faculdade costuma morrer |

**Se ele aprofundar:** "o que você faria diferente hoje?" Uma resposta honesta
vale mais que uma defesa. Sugestão verdadeira: eu teria escrito as regras de
negócio como funções puras desde o início, e não só da metade em diante. Foi o
que deixou a cobertura chegar a 91%, porque função pura não precisa de banco
para ser testada, e eu só percebi isso no meio do caminho.

---

#### 3. Onde fica o ponto de entrada? O que acontece na inicialização?

**Abra:** `backend/app/main.py`

Quatro coisas acontecem, nesta ordem:

1. **Linha 23 a 28.** Se o ambiente for produção, o sistema confere a própria
   configuração e **se recusa a subir** se algum segredo estiver inseguro. Está
   em `config.py:75`, `validar_para_producao`. Ele checa chave JWT de exemplo ou
   curta demais, senha padrão do banco, webhook sem token, Google não
   configurado e site sem HTTPS.
2. **Linha 29 a 30.** Liga o agendador, que é quem envia as cobranças sozinho.
3. **Linha 43 a 49.** Libera o CORS, que é a permissão para o site em outro
   endereço chamar a API.
4. **Linha 59 a 66.** Registra os oito módulos, cada um com suas rotas.

**Se ele aprofundar:** "por que validar a configuração em vez de só documentar?"
Porque documentação não impede o erro. Subir em produção com a chave de exemplo
é o tipo de coisa que acontece às 23h de um domingo. Aqui o sistema simplesmente
não sobe, e a mensagem diz o que está errado.

O frontend tem o ponto de entrada dele em `frontend/src/main.ts`, que monta o
`AppComponent` com a configuração de `app.config.ts` (rotas, HTTP e o
interceptor).

---

### Configuração e ambiente

#### 4. Onde é a conexão com o banco? O que muda entre desenvolvimento e produção?

**Abra:** `backend/app/db/session.py` (linha 7) e `backend/app/core/config.py`
(linha 22).

> A conexão nasce em `session.py:7`, com `create_engine(settings.DATABASE_URL)`.
> O endereço não está escrito no código: vem de `DATABASE_URL`, uma variável de
> ambiente.
>
> `pool_pre_ping=True` manda testar a conexão antes de usar. Sem isso, uma
> conexão que o banco fechou por inatividade estoura na cara do usuário.
>
> O que muda entre os dois ambientes:

| | Desenvolvimento | Produção |
|---|---|---|
| Banco | container `db` no meu Docker | container no servidor da AWS |
| Senha | a do `.env` local | outra, só no servidor |
| `AMBIENTE` | `desenvolvimento` | `producao`, e aí a validação de segredos liga |
| Endereço da API no site | `http://localhost:8000` | `/api`, mesmo domínio |
| Agendador | ligado | ligado |

Os dois endereços do site estão em `frontend/src/environments/`, um arquivo para
cada ambiente. O Angular troca um pelo outro na hora de compilar.

---

#### 5. Quais variáveis de ambiente? Onde são lidas? Onde ficam em produção?

**Abra:** `.env.example` e `backend/app/core/config.py`

> O modelo está em `.env.example`, versionado. O arquivo real é o `.env`, que
> **nunca vai para o Git**: está no `.gitignore`.
>
> Todas são lidas em um lugar só: a classe `Settings` em `config.py`. Ela herda
> de `BaseSettings` do Pydantic, que lê as variáveis de ambiente sozinho e
> ainda converte o tipo (`JWT_EXPIRE_MINUTES` vira número, `AGENDADOR_ATIVO`
> vira booleano). Nenhum outro arquivo chama `os.getenv`: todos importam
> `settings`.

As principais: `DATABASE_URL`, `JWT_SECRET`, `GOOGLE_CLIENT_ID` e
`GOOGLE_CLIENT_SECRET`, `FRONTEND_URL`, `WEBHOOK_TOKEN`, `EVOLUTION_API_KEY`,
`ADMIN_EMAILS`, `PIX_CHAVE`.

> Em produção elas ficam no `.env` do servidor, que existe só lá, criado na mão.
> As credenciais do deploy ficam em outro lugar ainda: nos **Secrets do
> GitHub**, que o GitHub mostra uma vez e nunca mais, nem para mim.

**Se ele aprofundar:** "e se alguém commitar o .env por engano?" Está no
`.gitignore`, e a validação de produção pega o caso mais grave (segredo de
exemplo). Mas a resposta honesta é que, se vazasse, eu trocaria a chave JWT, o
que derrubaria todas as sessões, e trocaria a senha do banco.

---

#### 6. Clonei o repositório agora. Quais passos para rodar?

**Abra:** `COMO-RODAR.md`

Diga exatamente isto, e esteja pronta para executar:

```bash
cp .env.example .env
docker compose up
```

> Dois comandos. O primeiro cria o arquivo de configuração a partir do modelo,
> e os valores padrão já servem para desenvolvimento. O segundo sobe tudo:
> banco, API e interface.
>
> Depois: a interface em `http://localhost:4200` e a API em
> `http://localhost:8000`, com a documentação automática em `/docs`.
>
> A única coisa que não funciona com os valores padrão é o login com o Google,
> que precisa de credenciais do Google Cloud. Elas são pessoais e não podem ir
> para o repositório.

**Atenção na hora:** o Angular leva cerca de 50 segundos para compilar na
primeira vez. Se ele abrir o `localhost:4200` antes disso e não aparecer nada,
**não é erro**. Diga: "está compilando, leva uns 50 segundos na primeira vez".
Saber disso demonstra que você roda o projeto de verdade.

---

### Dados

#### 7. Quais são as entidades e como se relacionam?

**Abra:** `backend/app/db/base.py`. Ele lista todas as dez num lugar só.

Desenhe:

```
VENDEDOR  (dono da conta, vem do Google)
   |
   |--1:1-->  CONFIGURACAO     (horarios, canal do resumo, envio automatico)
   |
   |--1:N-->  CLIENTE          (nome, whatsapp, cpf, endereco)
   |             |
   |             |--1:N--> VENDA         (valor total, numero de parcelas)
   |             |            |
   |             |            +--1:N--> PARCELA  (valor, vencimento, pagamento)
   |             |
   |             +--1:N--> RESPOSTA_DEVEDOR   (o "1 - ja paguei")
   |
   |--1:N-->  TEMPLATE_MENSAGEM   (os textos: lembrete, vencimento, atraso)
   |--1:N-->  COBRANCA_LOG        (historico do que foi enviado)
   |--1:1-->  ASSINATURA          (teste gratis, ativa ou vencida)
                 |
                 +--1:N--> PAGAMENTO_ASSINATURA  (os comprovantes em Pix)
```

**Onde está no código:** cada entidade é um arquivo `models.py` dentro do seu
módulo. `backend/app/modules/clientes/models.py`,
`backend/app/modules/vendas/models.py`, e assim por diante.

**Dois detalhes que valem ponto:**

1. Em `clientes/models.py:15`, uma restrição de unicidade: o mesmo número de
   WhatsApp não pode se repetir **dentro da mesma conta**, mas pode existir em
   contas diferentes. Duas sacoleiras podem vender para a mesma pessoa.
2. Em `vendas/models.py:31`, a venda tem `cascade="all, delete-orphan"` nas
   parcelas: apagar a venda apaga as parcelas dela, nunca sobra parcela órfã.

---

#### 8. Mostre a última migração e explique.

**Abra:** `backend/alembic/versions/b7c4e1f90a32_numero_do_cliente_com_codigo_do_pais.py`

Para confirmar que é a última: `docker compose exec backend alembic heads`
devolve `b7c4e1f90a32 (head)`.

Esta migração é a melhor do projeto para mostrar, porque ela **conserta um bug
real de produção**. Conte a história:

> Antes da regra RN-C01, nada conferia o telefone, e clientes foram cadastrados
> sem o código do país. O WhatsApp exige o 55 na frente: uma cobrança mandada
> para "4799..." simplesmente **não chega a ninguém, e nenhum erro aparece no
> caminho**. A falha só apareceria meses depois, pela boca do vendedor, como "o
> cliente disse que nunca recebeu".
>
> A migração varre a tabela e acrescenta o 55 em quem tem 10 ou 11 dígitos, que
> é o formato brasileiro sem código do país. Número de outro tamanho fica
> intocado, porque pode ser de fora e já ter o código certo.
>
> A parte da qual eu mais gosto é a linha 68 a 85. O banco não deixa dois
> clientes do mesmo vendedor com o mesmo número. Se o mesmo telefone estivesse
> salvo em dois formatos na mesma carteira, corrigir os dois criaria o conflito
> e a migração explodiria no meio, deixando o banco pela metade. Então ela
> **confere antes** e, se for acontecer, **para e avisa** qual cliente é, para
> eu juntar os cadastros na mão.
>
> E o CPF: ela tira ponto e traço, mas **não apaga** CPF que não passa na conta
> dos dígitos verificadores. Apagar dado de cliente por causa de uma regra nova
> seria pior que o dado torto. Ele é corrigido na próxima edição do cadastro,
> quando a API recusa o valor inválido.
>
> A `downgrade`, na linha 104, desfaz: tira o 55 de volta.

**Se ele aprofundar:** "por que toda migração tem downgrade?" Porque se a
versão nova der problema em produção, eu preciso conseguir voltar. Migração sem
volta é caminho só de ida.

---

#### 9. Onde está o filtro por usuário?

Esta é a pergunta de segurança mais provável. Mostre **dois** lugares, porque a
resposta completa tem duas partes.

**Primeiro, de onde vem a identidade.** Abra
`backend/app/modules/auth/deps.py`, linha 13:

> `get_current_vendedor_id` pega o token do cabeçalho `Authorization`, confere a
> assinatura e a validade, e devolve o id do vendedor. Se não tiver token, ou se
> estiver vencido ou adulterado, responde 401 e a requisição morre aqui.
>
> O ponto importante: **o id vem do token assinado, nunca do que o navegador
> mandou no corpo ou na URL**. Não existe parâmetro `vendedor_id` que alguém
> possa trocar.

**Segundo, onde ele é aplicado.** Abra
`backend/app/modules/clientes/repository.py`:

> Todos os métodos recebem `vendedor_id` e filtram por ele. Linha 16,
> `listar`: `where(Cliente.vendedor_id == vendedor_id)`. Linha 21,
> `buscar_por_id`: filtra pelo id **e** pelo vendedor, então pedir o id de um
> cliente de outra conta devolve nada, que o service transforma em 404.
>
> Isso vale para o repository de todos os módulos, porque o repository é a
> **única** camada que toca o banco. É uma convenção do projeto, e está escrita
> no `CLAUDE.md`.

**O teste que prova:** `backend/tests/test_api_clientes.py:111`, classe
`TestIsolamentoEntreContas`. Ele cadastra um cliente com uma conta, cria uma
segunda conta, e confere que a segunda recebe lista vazia.

---

### Autenticação e segurança

#### 10. Como é a autenticação? Onde o token é gerado, validado, e quando expira?

**Conte o fluxo inteiro**, abrindo `backend/app/modules/auth/router.py`:

> 1. A pessoa clica em "Entrar com Google". O frontend manda o navegador para
>    `/auth/google/login` (linha 21), que redireciona para o Google.
> 2. O Google autentica (a senha é digitada lá, não aqui) e devolve o navegador
>    para `/auth/google/callback` (linha 27) com um código de uso único.
> 3. O backend troca esse código pelos dados da pessoa, nos bastidores
>    (`google_client.py`).
> 4. `AuthService.login_ou_cadastro` (em `service.py:13`) procura o e-mail. Se
>    não existir, **cria o vendedor e começa o período de teste**. Se existir,
>    recupera.
> 5. Emite o JWT: `core/security.py:12`, `criar_access_token`. Algoritmo HS256,
>    conteúdo mínimo (só o id do vendedor e a expiração), assinado com a
>    `JWT_SECRET`.
> 6. Redireciona para o site com o token **no fragmento da URL**, depois do `#`.

**Destaque o detalhe do `#`** (linha 51 do router), porque é uma decisão
consciente:

> O token vai depois do `#`. Essa parte da URL **não é enviada a servidor
> nenhum**: fica só no navegador. Se eu mandasse como parâmetro normal
> (`?token=`), ele apareceria no log do servidor, no histórico e no cabeçalho
> `Referer` de qualquer link que a pessoa clicasse depois.

**Validação:** `core/security.py:19`, `validar_access_token`. Ela decodifica,
confere assinatura e expiração, e devolve `None` em qualquer problema.

**Expiração:** `JWT_EXPIRE_MINUTES = 1440`, ou seja **24 horas**
(`config.py:26`). Depois disso o token é recusado, o frontend recebe 401 e
manda a pessoa para o login.

**Se ele aprofundar:** "por que não tem refresh token?" Porque o custo de
reautenticar é um clique, já que a senha está no Google e o navegador costuma
manter a sessão de lá. Refresh token traz uma lista de tokens revogados para
manter, e para um sistema de uso diário isso é complexidade sem retorno.

**Se ele aprofundar:** "e se roubarem o token?" Quem tiver o token age como a
pessoa até ele vencer. É a limitação real do modelo. Mitigações no projeto:
validade curta, HTTPS obrigatório (o Nginx redireciona todo HTTP e manda
`Strict-Transport-Security`), e o token nunca aparece em URL navegável.

---

#### 11. Como funciona a autorização? Mostre uma rota bloqueada.

Autenticação é "quem é você". Autorização é "o que você pode". O sistema tem
**três níveis**, e mostrar os três é a resposta completa.

**Nível 1, estar logado.** `backend/app/modules/clientes/router.py:28`:
`Depends(get_current_vendedor_id)`. Sem token, 401.

**Nível 2, ter assinatura em dia.** Abra
`backend/app/modules/assinatura/deps.py:37`, `exigir_assinatura_ativa`.

> Repare na diferença dentro do mesmo arquivo de rotas: `listar_clientes`
> (linha 28) usa `get_current_vendedor_id`, mas `cadastrar_cliente` (linha 37)
> usa `exigir_assinatura_ativa`. **Ler é sempre liberado; escrever exige
> assinatura.** Quem está com a assinatura vencida continua vendo tudo o que é
> seu, e isso foi de propósito: prender o dado da pessoa como refém seria
> indefensável.
>
> A recusa é **402 Pagamento Necessário**, que é um código HTTP que existe
> exatamente para isto.

**Nível 3, ser administradora.** Mesmo arquivo, linha 58, `exigir_admin`,
responde 403. A lista de administradores vem da variável `ADMIN_EMAILS`, e não
de uma coluna no banco. O motivo está escrito no `config.py:48`: assim **não
existe bit a inverter**, ninguém vira administrador por gravação no banco.

**No frontend também, mas por outro motivo.** Abra
`frontend/src/app/core/auth.guard.ts`.

> O guard impede abrir a tela sem estar logado. Mas isso é **conforto, não
> segurança**: o navegador está na máquina da pessoa e qualquer um pode
> contornar. A porta de verdade é sempre a do servidor. Tem até um comentário
> dizendo isso em `auth.service.ts:44`: "Só decide o que mostrar no menu. A
> porta de verdade é o 403 do servidor".

**Se ele aprofundar e mandar você provar:** apague temporariamente o
`canActivate: [authGuard]` de uma rota em `app.routes.ts`, abra a tela, e
mostre que ela abre mas **não carrega dado nenhum**, porque a API responde 401.
Isso prova que a segurança não depende do frontend.

---

#### 12. Como as senhas são guardadas? O que protege contra SQL injection e XSS?

**Senhas:** a resposta é curta e forte.

> O sistema **não guarda senha nenhuma**. Não existe campo de senha, nem tabela,
> nem hash. A autenticação é inteiramente pelo Google. Dá para conferir: o
> modelo `Vendedor` em `vendedores/models.py` tem e-mail, nome, foto e ativo,
> e mais nada.

**Dados sensíveis:** CPF e telefone de clientes ficam no banco sem criptografia
de coluna, mas:

- o banco não tem porta aberta para a internet, só a rede interna do Docker;
- o acesso é sempre pela API, sempre filtrado por conta;
- os comprovantes de Pix ficam num volume fora de qualquer pasta pública e só
  saem por endpoint autenticado da administradora (`docker-compose.yml:42`).

**SQL injection:**

> Não construo SQL concatenando texto. Uso o SQLAlchemy, que sempre manda os
> valores separados do comando (consulta parametrizada). Em
> `clientes/repository.py:16`, `select(Cliente).where(Cliente.vendedor_id ==
> vendedor_id)` vira um comando com marcador, e o valor viaja à parte. Não existe
> ponto em que texto do usuário entre no comando.
>
> Nas migrações eu uso `sa.text()` com SQL escrito, mas sempre com parâmetro
> nomeado, nunca com valor colado. Veja a linha 88 da última migração:
> `{"n": numero, "i": id_cliente}`.

**XSS:**

> O Angular escapa automaticamente tudo o que entra no template. Se alguém
> cadastrar um cliente chamado `<script>alert(1)</script>`, aquilo aparece na
> tela **como texto**, não executa. Para escapar disso eu teria que usar
> `innerHTML` ou `bypassSecurityTrust` de propósito, e o projeto não usa nenhum
> dos dois.
>
> Além disso, o Nginx manda os cabeçalhos de segurança (`taemdia.conf:21-24`):
> `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` contra
> clickjacking, e `Strict-Transport-Security`.

**Mostre os testes:** `backend/tests/test_seguranca.py`, 20 testes de controles
de segurança, incluindo a proteção do webhook e a validação de produção.

---

### Regras de negócio e fluxo

#### 13. Abra o arquivo da funcionalidade principal e explique a regra.

Escolha **`backend/app/modules/vendas/service.py`**. É o coração.

Explique três funções, nesta ordem:

**`_dividir_valor`, linha 39.** O problema: R$ 100,00 em 3 vezes dá 33,333...

> Eu converto tudo para centavos inteiros, divido, e **jogo os centavos que
> sobram nas últimas parcelas**. Dá 33,33 + 33,33 + 33,34, e a soma fecha
> exatamente em 100,00. Se eu arredondasse cada parcela, a soma daria 99,99 ou
> 100,02, e o cliente pagaria valor diferente do combinado.
>
> E uso `Decimal`, nunca ponto flutuante, porque em ponto flutuante 0,1 + 0,2
> não dá 0,3.

**`_somar_meses`, linha 29.** O problema: 31 de janeiro mais um mês.

> Não existe 31 de fevereiro. A função ajusta para o último dia do mês: 31/01
> vira 28/02, e em ano bissexto vira 29/02. Sem isso o sistema quebraria em
> toda venda feita no fim do mês.

**`calcular_status`, linha 52.** O ciclo de vida da parcela, na ordem correta:

```python
if parcela.data_pagamento is not None:   return "paga"
if parcela.aguardando_confirmacao:       return "aguardando_confirmacao"
if parcela.data_vencimento < hoje:       return "atrasada"
return "pendente"
```

> A ordem importa. "Paga" vem primeiro de propósito: se o cliente respondeu "já
> paguei" e **depois** o vendedor confirmou, a parcela está paga, não aguardando.
> Tem um teste só para isso: `test_paga_tem_prioridade_sobre_aguardando`.
>
> E repare no `<`, não `<=`. Parcela que vence **hoje** ainda está pendente, não
> atrasada. A pessoa tem o dia todo para pagar.

**Se ele mandar você explicar linha a linha**, use esse `<` como o detalhe de
ouro. É uma linha de código e uma decisão de negócio ao mesmo tempo.

---

#### 14. E se o usuário mandar dado inválido? A validação está onde?

**Resposta curta: nos dois lados, de propósito, e por motivos diferentes.**

> No formulário, para a pessoa ver o erro na hora, sem esperar a rede. Na API,
> porque **o formulário pode ser contornado**: qualquer um chama a API direto,
> com um comando de terminal, sem passar pela minha tela. Validação só no
> navegador não é validação, é sugestão.
>
> Tem até um comentário dizendo isso em `clientes/schemas.py:22`.

**Mostre a validação da API.** Abra `backend/app/modules/clientes/schemas.py`:

- Linha 26: `nome` entre 2 e 120 caracteres.
- Linha 28: `whatsapp_numero` entre 8 e 24 caracteres (cabe a pontuação).
- Linha 33: `cpf` até 14 caracteres (cabe "529.982.247-25").
- Linha 36: `conferir_cpf` roda a conta dos dígitos verificadores de verdade.
- Linha 41: `conferir_whatsapp` é um `model_validator` e não um
  `field_validator`, porque ele depende de **dois** campos: o número e o código
  do país.

**Mostre que a regra não está duplicada.** Abra
`backend/app/modules/clientes/regras.py`:

> As regras são funções puras, sem banco e sem HTTP, num arquivo só. O schema as
> usa. E tem um espelho em TypeScript, em
> `frontend/src/app/core/regras-cliente.ts`, para o formulário poder validar sem
> ir à rede.
>
> Dois arquivos com a mesma regra é risco de um envelhecer. Por isso existe
> `backend/tests/test_regras_espelhadas.py`: um teste que **falha** se os dois
> saírem de sincronia.

**O que a pessoa vê:** erro de formato devolve **422** (o FastAPI faz sozinho a
partir do schema). Número repetido na mesma conta devolve **409**, e a tela
mostra "Já existe um cliente com esse número de WhatsApp".

---

#### 15. Como os erros são tratados e registrados? Onde eu veria um erro em produção?

**Três camadas. Mostre as três.**

**1. Erros esperados, no backend.** O service levanta uma exceção com nome de
negócio (`WhatsappDuplicadoError`, em `clientes/service.py:9`), e o router
traduz para o código HTTP certo (`router.py:41`, vira 409).

> Isso é de propósito: o service não sabe o que é HTTP. Se amanhã essa regra
> for usada por outra coisa que não seja uma API, ela continua valendo.

**2. Erros no frontend.** Abra `frontend/src/app/core/auth.interceptor.ts`:

> Dois casos são tratados num lugar só, para todas as telas:
> **401** encerra a sessão e volta para a entrada. **402** abre um diálogo
> explicando que a assinatura venceu.
>
> E repare na linha 39: o diálogo só abre se foi uma **ação** da pessoa, não uma
> leitura. Se abrir uma tela disparasse o aviso, a pessoa levaria um pop-up sem
> ter feito nada.
>
> Fora isso, cada tela tem três estados desenhados: carregando, vazio e erro.
> Estão em `frontend/src/app/core/`, nos componentes `esqueleto`,
> `estado-vazio` e `estado-erro`.

**3. Onde eu veria em produção.** Seja concreta:

```bash
docker compose -f docker-compose.prod.yml logs backend --tail 100
```

> Pelo Session Manager da AWS, que é um terminal no navegador, sem SSH. O
> agendador registra com `logger.exception` (`agendador.py:58`), que grava o
> rastro completo do erro. E ele captura a exceção de propósito: **o agendador
> nunca pode derrubar a aplicação**. Uma falha no envio de uma cobrança não pode
> tirar o sistema inteiro do ar.

**Se ele aprofundar:** "e monitoramento?" Resposta honesta: não tem ferramenta
de monitoramento (tipo Sentry). O que existe é o log no servidor e a conferência
automática no fim do deploy, que acessa o site e falha se ele não responder.
Para o tamanho do projeto, foi uma escolha consciente de escopo.

---

### Integrações

#### 16. Como o frontend fala com o backend?

**Abra, nesta ordem:**

1. `frontend/src/app/core/api.config.ts`: o endereço base, que vem do arquivo de
   ambiente.
2. `frontend/src/app/core/clientes.service.ts`: a chamada em si,
   `this.http.post<Cliente>(...)`. Um serviço por assunto, e as telas nunca
   chamam `HttpClient` direto.
3. `frontend/src/app/core/auth.interceptor.ts:26`: o token sendo carimbado em
   toda requisição, automaticamente. Nenhuma tela precisa lembrar disso.
4. A volta: no componente, `.subscribe({ next: ..., error: ... })`.

> A comunicação é HTTP com JSON. Em desenvolvimento o site está na porta 4200 e
> a API na 8000, dois endereços diferentes, e por isso o backend precisa liberar
> CORS (`main.py:43`). Em produção os dois ficam no mesmo endereço e o CORS
> deixa de ser necessário, porque o Nginx põe a API sob `/api`.

**Detalhe que vale ponto.** Abra `frontend/src/app/core/clientes.service.ts:12`:

> O campo `whatsapp_formatado` vem **pronto da API**. É um `computed_field` do
> Pydantic (`schemas.py:85`). Eu poderia formatar na tela, mas aí a regra de
> formatação existiria em dois lugares e um dia eles discordariam. A API manda
> formatado, e o site só exibe.

---

#### 17. Usa serviço externo? E se ele cair?

**Três serviços externos.** Para cada um, saiba o que acontece se ele cair.

| Serviço | Para quê | Se cair |
|---|---|---|
| **Google OAuth** | O login | Ninguém entra. Quem já está dentro continua, porque o token vale 24h e não depende do Google. O `callback` captura `httpx.HTTPError` e responde 400 com mensagem clara (`auth/router.py:33`) |
| **Evolution API (WhatsApp)** | Enviar as cobranças | O envio falha, mas **o sistema inteiro continua funcionando**. É aqui que está a melhor parte da arquitetura, veja abaixo |
| **AWS** | Onde tudo roda | Site fora do ar |

**Mostre a abstração do WhatsApp.** Abra
`backend/app/modules/whatsapp/client.py`. É a decisão de desacoplamento mais
bem feita do projeto:

> Nenhum módulo do sistema importa a biblioteca de WhatsApp. Todos falam com um
> **contrato**, a interface `WhatsAppClient` da linha 36, que tem três métodos:
> enviar, status e desconectar.
>
> Existem duas implementações desse contrato. A real, que chama a Evolution API,
> e o `SimuladorWhatsAppClient` da linha 46, que registra a mensagem no log sem
> mandar nada.
>
> Isso me permitiu desenvolver e testar **todo** o motor de cobrança (o
> agendamento, os templates, as regras de horário, o limite diário, o histórico)
> sem depender de um celular ligado. E permite trocar a Evolution por outra
> coisa mexendo em um arquivo.

---

### Testes e qualidade

#### 18. Quais testes existem? Rode agora. Mostre a cobertura.

**Rode na frente dele:**

```bash
docker compose exec backend pytest
```

Leva cerca de 2 minutos. O resultado esperado: **492 passed**, cobertura
**91%**.

```bash
docker compose --profile testes run --rm frontend-testes
```

Resultado esperado: **178 de 178 SUCCESS**, Statements **66,2%**.

> As metas do playbook são 75% no backend e 25% no frontend. Estou em 91% e
> 66%. E a meta não é promessa: no frontend ela está configurada em
> `karma.conf.js:35`, e **o comando falha** se a cobertura cair abaixo de 25%. O
> CI reprova o envio.

**Explique um teste.** Escolha `backend/tests/test_vendas_calculos.py:16`:

```python
def test_soma_fecha_com_o_total_mesmo_com_dizima(self):
    valores = _dividir_valor(100.0, 3)
    assert sum(valores) == Decimal("100.00")
    assert valores == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
```

> Ele prova que dividir 100 em 3 fecha exatamente em 100, com o centavo que
> sobra na última parcela. É um teste rápido porque `_dividir_valor` é uma
> **função pura**: não precisa de banco, nem de servidor, nem de token. Foi
> escrever as regras assim que permitiu a cobertura alta.

**Fale dos testes de guarda, que são o diferencial do projeto.** Vários testes
não testam código Python: eles leem **arquivos de configuração** e falham se
estiverem errados.

| Arquivo | O que protege |
|---|---|
| `test_rotas_no_nginx.py` | Toda rota da API tem caminho no Nginx |
| `test_topologia_producao.py` | O compose de produção está coerente |
| `test_documentos_legais.py` | As páginas legais existem, abrem **sem login** e têm contato de verdade |
| `test_regras_espelhadas.py` | As regras em Python e em TypeScript não divergiram |
| `test_cobertura_frontend.py` | A lista de arquivos medidos continua completa |
| `test_guardas_ativas.py` | **Nenhum teste de guarda está pulando em silêncio** |

> O último é o meu favorito, e nasceu de um erro real. Os testes de guarda
> procuram arquivos fora da pasta do backend. Quando um deles não acha o
> arquivo, ele **pula**, e teste que pula é verde na tela. Eu tive cinco envios
> seguidos com o CI vermelho por causa de um arquivo de 0 byte que o Docker
> criou e que foi commitado por engano. A busca achava o arquivo vazio primeiro
> e lia nada. A correção foi `backend/tests/caminhos.py`, que ignora arquivo
> vazio, mais esse teste que vigia os vigias.

---

#### 19. Se eu mudar uma regra, qual teste falha? Faça.

**Esta você já tem ensaiada.** O roteiro verificado está na Parte 5, ensaio 2.

Resumo: abra `backend/app/modules/vendas/service.py` linha 59, troque `<` por
`<=`, rode `docker compose exec backend pytest tests/test_vendas_calculos.py -q
--no-cov`, e o resultado é **1 failed, 20 passed**, com o teste
`test_vence_hoje_ainda_e_pendente` apontado pelo nome.

---

### CI/CD e deploy

#### 20. Como executar as integrações manualmente, e não a cada merge?

**Abra:** `.github/workflows/ci.yml`, as linhas 3 a 7.

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

> Hoje roda em dois gatilhos: envio para a `main` e abertura de pull request.
> Para passar a manual, eu troco esse bloco por:
>
> ```yaml
> on:
>   workflow_dispatch:
> ```
>
> `workflow_dispatch` põe um botão "Run workflow" na aba Actions do GitHub, e o
> fluxo só roda quando alguém clica.
>
> No Deploy eu já uso os dois juntos: `.github/workflows/deploy.yml:26-32` tem
> `workflow_run` (automático, depois do CI) **e** `workflow_dispatch` (manual),
> para eu conseguir subir sem precisar enviar código.

**Se ele aprofundar:** "você faria isso?" Não, e o motivo é concreto: a graça do
CI é rodar sem alguém lembrar. Manual, o teste fica para depois e vira nunca. O
que eu faria, se o custo de minutos virasse problema, é filtrar por caminho
(`paths`), para não rodar a suíte inteira quando só a documentação mudou.

---

#### 21. Quais etapas o pipeline roda, em que ordem, e o que acontece se falhar?

**Abra:** `.github/workflows/ci.yml`

> O CI tem **dois jobs que rodam em paralelo**, porque não dependem um do outro.
>
> **Backend** (linha 10): sobe um PostgreSQL de verdade como serviço, instala o
> Python 3.12, instala as dependências, roda o pytest com cobertura, guarda o
> relatório, e roda a análise estática no SonarCloud se o token estiver
> configurado.
>
> **Frontend** (linha 68): instala o Node 20, `npm ci`, **compila** a aplicação,
> e só então roda os testes com cobertura num Chrome sem tela.
>
> Repare que compilar vem antes de testar. Erro de TypeScript aparece na
> compilação, que é mais rápida que a suíte inteira.

**O que acontece quando falha:**

> O job fica vermelho, o commit fica com um X no GitHub, e **o Deploy não
> acontece**. Isso não é por acaso: `deploy.yml:48-50` tem a condição
> `github.event.workflow_run.conclusion == 'success'`. Teste quebrado não vira
> site no ar.
>
> O relatório de cobertura é guardado **mesmo quando falha** (`if: always()`,
> linha 56), porque é quando eu mais preciso dele.

**Uma armadilha que eu encontrei nesse pipeline**, e que vale contar:

> Eu tinha um comando que canalizava a saída do pytest para o `tail`. No shell,
> isso faz o código de saída ser o do `tail`, não o do pytest. O CI parecia
> verde com dez testes falhando. A correção é redirecionar para arquivo e ler o
> código, ou usar `PIPESTATUS`.

---

#### 22. Onde está hospedado, como é o deploy, e como voltar atrás?

**Hospedagem:**

> Numa máquina EC2 da AWS, Ubuntu, região Ohio. O domínio é
> `taemdia.duckdns.org`, com HTTPS. Rodam cinco containers: Nginx, o site, a
> API, o agendador e o PostgreSQL.
>
> A porta 22, de SSH, está **fechada**. Eu entro na máquina pelo Session
> Manager da AWS, que é um terminal no navegador, sem senha, sem chave e sem
> porta aberta.

**Deploy:** abra `.github/workflows/deploy.yml` e `docs/deploy-automatico.md`.

> `git push` é tudo. O caminho:
>
> 1. O CI roda os testes.
> 2. Se passar, o Deploy compila as imagens Docker e as guarda no GitHub.
> 3. O GitHub pede à AWS, e a AWS manda a máquina baixar e trocar.
> 4. O robô acessa o site e **falha se ele não responder**.
>
> Duas decisões aqui. **A compilação acontece no GitHub**, não no servidor: o
> servidor tem 909 MB de memória e levava de 5 a 10 minutos para compilar o
> Angular, usando disco como memória. Agora ele só baixa, e a troca leva
> segundos.
>
> E o deploy roda **sobre o commit que o CI testou** (`deploy.yml:66`), não
> sobre o topo da branch. Entre um e outro pode ter entrado código que ninguém
> testou.

**Como voltar atrás.** Esta é a parte da pergunta que mais gente erra. Seja
concreta:

> Cada imagem é marcada com o código do commit
> (`deploy.yml:95`, a tag é o SHA), além de `latest`. Para voltar, eu entro pelo
> Session Manager e subo a versão anterior pelo número dela:
>
> ```bash
> cd /home/ubuntu/TaEmDia
> VERSAO=<sha-do-commit-bom> docker compose -f docker-compose.prod.yml up -d
> docker compose -f docker-compose.prod.yml restart nginx
> ```
>
> As imagens antigas ficam guardadas por 72 horas (`docker image prune` com
> filtro `until=72h`), então a volta é imediata.
>
> O `restart nginx` **não é opcional**, e eu aprendi isso na prática: subir os
> containers dá a eles endereço interno novo, o Nginx continua procurando no
> antigo, e o site responde **502**. Está escrito como passo obrigatório no
> script e documentado.

**Se ele aprofundar:** "e se a migração do banco já tiver rodado?" Aí voltar a
imagem não basta, porque o banco está à frente do código. Por isso toda migração
tem `downgrade`: eu rodaria `alembic downgrade -1` antes. É o cenário mais
delicado de um rollback, e vale dizer que você sabe disso.

---

### Processo e histórico

#### 23. Escolha um commit seu e explique.

**Prepare um antes.** Não escolha na hora.

Use este:

```bash
git log --oneline --all | grep -i "codigo do pais"
git show <o-hash>
```

Se não achar, use o da migração: o arquivo
`b7c4e1f90a32_numero_do_cliente_com_codigo_do_pais.py`. Rode:

```bash
git log --oneline -- backend/alembic/versions/b7c4e1f90a32_numero_do_cliente_com_codigo_do_pais.py
```

Conte a história completa (é a mesma da pergunta 8): **um bug que já estava em
produção, silencioso, que faria as cobranças não chegarem a ninguém sem nenhum
erro aparecer**. O commit tem três partes: a regra nova que impede novos casos,
a migração que conserta os antigos, e os testes.

**Sobre pull request e squad:** você fez o projeto sozinha. Diga a verdade, e
diga o que fez no lugar:

> Trabalhei sozinha, então não tive revisão de colega. O que usei no lugar foi
> revisão automática: o CI roda 492 testes e a análise estática do SonarCloud a
> cada envio, e os testes de guarda conferem coisas que uma pessoa esqueceria,
> como "a rota nova tem caminho no Nginx" e "as regras em Python e em TypeScript
> continuam iguais".

---

#### 24. Qual foi o bug mais difícil?

**Tenha dois na manga.** O primeiro é o melhor, mas o segundo mostra outra
habilidade.

**Bug 1, o telefone sem o código do país.** O mais importante, porque era
silencioso.

> Nada conferia o telefone, e números foram salvos sem o 55. O WhatsApp exige o
> código do país: a mensagem para "4799..." não chega, e **nenhum erro aparece
> em lugar nenhum**. O envio é dado como feito. O log diz sucesso.
>
> Eu não descobri por um erro: descobri lendo o código da integração para
> escrever a validação de campos. A correção tem três partes: a regra
> (`clientes/regras.py`, `normalizar_telefone`), a migração que conserta os
> cadastros antigos, e os testes. É o commit da pergunta 23.
>
> A lição: bug que não grita é pior que bug que derruba o sistema.

**Bug 2, o CI vermelho cinco vezes seguidas.** Mostra método de depuração.

> O CI quebrou cinco envios seguidos e o erro não fazia sentido: um teste de
> guarda reclamava do `docker-compose.prod.yml`, que estava correto.
>
> A causa: o Docker monta esse arquivo para dentro do container, e quando a
> montagem falha ele **cria um arquivo vazio no disco**. Alguns desses arquivos
> de 0 byte foram commitados. A busca dos testes subia as pastas procurando o
> arquivo e achava o vazio primeiro, lendo nada.
>
> Descobri comparando o que o teste lia com o que eu via no editor. A correção
> foi criar `backend/tests/caminhos.py`, que **ignora arquivo de tamanho zero**,
> pôr os restos no `.gitignore`, e escrever `test_guardas_ativas.py`, que falha
> se algum teste de guarda estiver pulando em silêncio.

**Se ele aprofundar:** "como você depura?" Diga a verdade do projeto, que é uma
disciplina real: **medir antes de concluir**. Por exemplo, para conferir
responsividade e contraste eu não olho a tela: tenho um teste
(`frontend/src/app/tema-escuro.spec.ts`) que monta cada tela e **calcula** o
contraste de todo texto. Foi ele que achou seis problemas de contraste que o
olho não pegou.

---

### Mudança ao vivo

#### 25. Adicione um campo a uma entidade e faça aparecer na tela.

**Esta você já tem ensaiada e cronometrada.** Veja a Parte 5, ensaio 3. Ele foi
executado de verdade e funciona.

A resposta que você dá **antes** de começar a digitar, para mostrar que entende
a arquitetura:

> Vou acrescentar o campo "observação" ao cliente. Preciso mexer em seis lugares,
> em quatro camadas, e eles têm uma ordem:
>
> 1. **O modelo**, que é a tabela.
> 2. **A migração**, porque o banco não muda sozinho.
> 3. **Os schemas**, para a API aceitar na entrada e devolver na saída.
> 4. **O service**, porque ele monta o objeto campo a campo.
> 5. **O serviço do frontend**, o contrato de tipos.
> 6. **A tela**, o campo no formulário.
>
> E tem uma pegadinha que eu conheço: o banco de testes é outro e não recebe a
> migração, então eu preciso recriá-lo ou os testes quebram.

Dizer isso **antes** vale mais que a mudança em si.

---

## Parte 5. Os três ensaios

Faça cada um pelo menos duas vezes, sozinha, antes da prova. Os três foram
executados neste repositório antes de serem escritos aqui.

### Ensaio 1. Rodar os testes e mostrar a cobertura

```bash
docker compose up -d
```

Espere cerca de 50 segundos.

```bash
docker compose exec backend pytest
```

**Resultado esperado:** `492 passed`, e no fim a linha `TOTAL ... 91%`.

```bash
docker compose --profile testes run --rm frontend-testes
```

**Resultado esperado:** `Executed 178 of 178 SUCCESS` e `Statements : 66.2%`.

Para mostrar o relatório visual: o arquivo `backend/htmlcov/index.html` abre no
navegador e mostra arquivo por arquivo, com as linhas não cobertas em vermelho.

---

### Ensaio 2. Quebrar uma regra e ver o teste falhar

**Verificado. O resultado abaixo é o que realmente sai.**

1. Abra `backend/app/modules/vendas/service.py` e vá na **linha 59**:

```python
    if parcela.data_vencimento < hoje:
        return "atrasada"
```

2. Troque `<` por `<=`.

3. Explique **antes de rodar** o que vai acontecer:

   > Isso faz uma parcela que vence hoje já contar como atrasada. É uma mudança
   > de uma letra, mas muda a regra de negócio: a pessoa perde o dia para pagar.
   > O teste que deve falhar é o `test_vence_hoje_ainda_e_pendente`.

4. Rode:

```bash
docker compose exec backend pytest tests/test_vendas_calculos.py -q --no-cov
```

5. **Saída real:**

```
FAILED tests/test_vendas_calculos.py::TestStatusDaParcela::test_vence_hoje_ainda_e_pendente
1 failed, 20 passed in 6.61s
```

6. **Desfaça**, voltando `<=` para `<`, e rode de novo para mostrar os 21
   passando.

**Por que esta é a melhor escolha de regra para quebrar:** a mudança é de um
caractere (rápido de fazer e de desfazer sob pressão), falha **um** teste só
(fica limpo na tela), e o nome do teste explica sozinho o que quebrou.

---

### Ensaio 3. Acrescentar um campo e fazer aparecer na tela

**Verificado de ponta a ponta.** Campo: `observacao` no cliente.

#### Passo 1. O modelo

`backend/app/modules/clientes/models.py`, depois da linha do `endereco`:

```python
    observacao: Mapped[str | None] = mapped_column(String, nullable=True)
```

> Por que `nullable=True`: clientes já cadastrados não têm esse valor. Coluna
> obrigatória numa tabela com dados precisa de um valor padrão, senão o banco
> recusa.

#### Passo 2. A migração

```bash
docker compose exec backend alembic revision --autogenerate -m "observacao do cliente"
```

**Saída real:** `Detected added column 'cliente.observacao'`.

> O Alembic compara os modelos com o banco e escreve a migração sozinho. Vale
> abrir o arquivo gerado e conferir, porque ele nem sempre acerta.

O arquivo gerado contém:

```python
def upgrade():
    op.add_column('cliente', sa.Column('observacao', sa.String(), nullable=True))
```

Aplique:

```bash
docker compose exec backend alembic upgrade head
```

#### Passo 3. Os schemas

`backend/app/modules/clientes/schemas.py`:

Em `ClienteCreate`, depois de `endereco`:
```python
    observacao: str | None = Field(default=None, max_length=300)
```

Em `ClienteOut`, depois de `endereco`:
```python
    observacao: str | None
```

#### Passo 4. O service

`backend/app/modules/clientes/service.py`, dentro de `cadastrar`, na construção
do `Cliente`:

```python
            observacao=dados.observacao,
```

> **Este é o passo que todo mundo esquece.** O service monta o objeto campo a
> campo, de propósito, e não com `**dados.model_dump()`. É mais verboso, mas
> impede que um campo novo do schema chegue ao banco sem alguém ter decidido
> isso. Se você pular este passo, o campo é aceito pela API, some, e a tela
> mostra vazio sem nenhum erro.

#### Passo 5. A pegadinha do banco de testes

**Rode os testes agora e eles falham:**

```
psycopg.errors.UndefinedColumn: column cliente.observacao does not exist
16 failed, 6 passed
```

> O banco de testes é outro (`taemdia_test`) e é criado com
> `Base.metadata.create_all`, que **cria tabela que falta mas não acrescenta
> coluna em tabela que já existe**. A migração rodou no banco de desenvolvimento,
> não nesse.

A correção, uma linha:

```bash
docker compose exec db psql -U taemdia -d postgres -c "DROP DATABASE IF EXISTS taemdia_test;"
```

O conftest recria na próxima execução. Rode de novo:

```bash
docker compose exec backend pytest tests/test_api_clientes.py -q --no-cov
```

**Saída real:** `22 passed`.

> Saber desta armadilha de antemão é o que separa "ela conhece o projeto" de
> "ela está tentando adivinhar". **Diga antes de acontecer.**

#### Passo 6. O contrato no frontend

`frontend/src/app/core/clientes.service.ts`:

Na interface `Cliente`:
```typescript
  observacao: string | null;
```

Na interface `ClienteCreate`:
```typescript
  observacao?: string | null;
```

#### Passo 7. A tela

`frontend/src/app/pages/clientes/clientes.component.ts`, três lugares:

No template, depois do campo de endereço:
```html
            <mat-form-field appearance="outline" class="campo">
              <mat-label>Observação</mat-label>
              <input matInput [(ngModel)]="novo.observacao" name="observacao" maxlength="300" />
            </mat-form-field>
```

No objeto `novo`, depois de `endereco: ''`:
```typescript
    observacao: '',
```

No envio, dentro de `this.service.criar({...})`:
```typescript
      observacao: this.novo.observacao.trim() || null,
```

E no reset depois de salvar, acrescente `observacao: ''`.

#### Passo 8. Conferir

O `ng serve` recompila sozinho em alguns segundos. Abra
`http://localhost:4200/clientes`, clique em cadastrar, e o campo está lá.

**Verificado:** `npx ng build` compila sem erro com essas mudanças.

#### Como desfazer

```bash
git checkout backend/app/modules/clientes/ frontend/src/app/core/clientes.service.ts frontend/src/app/pages/clientes/clientes.component.ts
docker compose exec backend alembic downgrade -1
rm backend/alembic/versions/*observacao*.py
docker compose exec db psql -U taemdia -d postgres -c "DROP DATABASE IF EXISTS taemdia_test;"
```

---

## Parte 6. Perguntas difíceis e como responder

### Sobre o uso de IA

Ela vai aparecer, de alguma forma. O playbook diz que usar não é proibido, mas
**não dispensa o domínio do resultado**.

A resposta boa é direta e sem defensiva:

> Usei assistente de IA, sim, principalmente para escrever código repetitivo
> mais rápido e para revisar o que eu escrevi. O que não deleguei foi a decisão.
> Cada escolha de arquitetura deste projeto eu consigo justificar e defender, e
> é o que estou fazendo agora. Se quiser, pode apontar qualquer arquivo e eu
> explico por que ele está escrito assim.

**O que você nunca deve dizer:** "a IA que fez isso", "não sei, foi gerado".

**O que torna isso verdade no seu caso, e você deve mencionar:** o projeto tem
um arquivo `CLAUDE.md` com uma seção chamada "Zona morta", que é uma lista dos
erros já cometidos no projeto, com a correção de cada um. Ela existe porque cada
linha ali custou tempo real. Mostrar esse arquivo é mostrar processo.

### Quando você não souber a resposta

**Nunca invente.** O professor percebe, e inventar é o que mais machuca numa
prova de autoria.

A fórmula que funciona:

> Não lembro de cabeça. Mas sei onde está: é em [módulo], no arquivo [X]. Posso
> abrir?

Saber onde procurar **é** domínio do codebase. Decorar não é.

Se não souber nem onde está:

> Essa parte eu teria que reler. O que eu sei é [o que você sabe de verdade
> sobre o assunto em volta].

### Se ele apontar um defeito real

Concorde, e mostre que você sabe o tamanho do problema:

> Tem razão. Isso é uma limitação. Eu escolhi [o que escolheu] porque [motivo],
> e o preço é exatamente esse. Se fosse crescer, eu resolveria com [solução].

**Limitações reais do projeto que você pode assumir sem medo:**

- Não tem ferramenta de monitoramento de erros em produção, só o log no
  servidor.
- O status da parcela ser calculado impede filtrar por status direto no SQL.
- Não tem refresh token: depois de 24 horas, login de novo.
- Os comprovantes de assinatura são conferidos na mão, não tem pagamento
  automático.
- A cobertura do frontend (66%) é menor que a do backend (91%), porque tela é
  mais cara de testar que função pura.

### Perguntas "e se" prováveis

| Pergunta | Resposta curta |
|---|---|
| "E se dois vendedores tiverem o mesmo cliente?" | Funciona. A restrição de unicidade é por `(vendedor_id, whatsapp_numero)`, não por número sozinho. Tem teste: `test_mesmo_numero_pode_existir_em_contas_diferentes` |
| "E se o cliente responder qualquer coisa no WhatsApp?" | É ignorado. `interpretar_resposta` em `cobrancas/regras.py:70` só aceita "1", "2" ou "3". Texto livre devolve `None` |
| "E se o vendedor cobrar a mesma pessoa dez vezes no dia?" | Não consegue. `MAX_MENSAGENS_DIA = 3` em `cobrancas/regras.py:12`, e o envio só acontece entre 8h e 20h |
| "E se o servidor cair no meio de um cadastro?" | A transação não é confirmada e nada é gravado pela metade. A tela diz exatamente isso: "Nada foi gravado pela metade" |
| "Como você escalaria para 10 mil vendedores?" | O gargalo seria o agendador, que hoje varre todos os vendedores num laço só. Eu o quebraria em fila de tarefas (Celery ou similar), e poria índice em `(vendedor_id, data_vencimento)` na parcela |
| "Por que não tem testes de ponta a ponta?" | Tem um: `backend/tests/test_fluxo_completo.py` faz o caminho inteiro, do cadastro à cobrança. O que não tem é teste de navegador dirigindo a tela, que foi escolha de escopo |

---

## Checklist da véspera

Marque cada um só depois de ter feito **de verdade**.

- [ ] Consigo desenhar o diagrama da Parte 1 no papel, sem olhar
- [ ] Sei dizer de cabeça o que faz cada uma das três camadas do backend
- [ ] `docker compose up` roda na minha máquina e eu sei que leva 50 segundos
- [ ] Rodei o Ensaio 1 e vi `492 passed` e `178 SUCCESS`
- [ ] Fiz o Ensaio 2 sozinha, sem olhar o guia, e desfiz
- [ ] Fiz o Ensaio 3 inteiro sozinha, inclusive a pegadinha do banco de testes
- [ ] Sei explicar por que o status da parcela não é guardado
- [ ] Sei mostrar, em dois arquivos, como um vendedor não vê dado de outro
- [ ] Sei explicar por que login com Google e não senha
- [ ] Tenho o commit da pergunta 23 escolhido e sei contar a história dele
- [ ] Tenho os dois bugs da pergunta 24 na ponta da língua
- [ ] Sei dizer três limitações do projeto sem ficar na defensiva

### No dia

- Leve o projeto **rodando** (`docker compose up` feito antes de entrar).
- Deixe abertas as abas: `main.py`, `clientes/router.py`,
  `clientes/repository.py`, `vendas/service.py`, `app.routes.ts`,
  `auth.interceptor.ts`.
- Deixe um terminal aberto na pasta do projeto.
- Abra o arquivo antes de responder. Sempre.
