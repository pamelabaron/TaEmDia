# Análise estática de código

O projeto usa **SonarQube Cloud** para analisar o código a cada envio: ele
procura bug provável, trecho repetido, complexidade alta e falha de segurança,
e cruza isso com o relatório de cobertura dos testes.

> **Sobre o nome.** Em outubro de 2024 a Sonar renomeou a família inteira. O
> SonarCloud virou SonarQube Cloud, o SonarQube virou SonarQube Server, e a
> edição grátis que se instala virou SonarQube Community Build. São o mesmo
> motor de análise em lugares diferentes. Aqui usamos o Cloud, hospedado pela
> própria Sonar, porque o servidor do projeto tem 909 MB de memória e o
> SonarQube instalado pede cerca de 4 GB só para ele.

## O que já está pronto

| | |
|---|---|
| Configuração | `sonar-project.properties`, na raiz |
| Passo no CI | `.github/workflows/ci.yml`, job `backend` |
| Conferência | `backend/tests/test_analise_estatica.py`, 7 testes |

Falta uma coisa só: **o token**. Sem ele o passo não roda, de propósito, para
que quem clonar o repositório não veja o CI quebrar por falta de um segredo
que não é dele.

## O que fazer, uma vez

### 1. Criar a conta

1. Entre em <https://sonarcloud.io> e clique em **Log in**
2. Escolha **With GitHub** e autorize

### 2. Criar a organização

A chave da organização precisa ser **`pamelabaron`**, porque é o que está no
`sonar-project.properties`. Se o site sugerir outra, pode trocar ali mesmo.

1. **Import an organization from GitHub**
2. Escolha a conta `pamelabaron`
3. Em "Choose a plan", escolha **Free plan**, que vale para repositório público
4. Confira que a **Key** ficou `pamelabaron`

### 3. Criar o projeto

1. **Analyze new project**
2. Marque o repositório **TaEmDia**
3. Confira que a **Project key** ficou `pamelabaron_TaEmDia`

> Se qualquer uma das duas chaves sair diferente, **não force**: anote o que
> saiu e acerte o `sonar-project.properties` para bater. Chave que não bate faz
> a análise ir para lugar nenhum, sem erro.

### 4. Escolher o método de análise. Este passo é o que mais dá problema

O SonarQube Cloud liga a **Análise Automática** sozinho em projeto novo. Ela é
incompatível com a análise pelo CI: as duas juntas não rodam, e o CI falha
dizendo que precisa desligar uma.

1. Na tela que pergunta o método, escolha **With GitHub Actions**
2. Se ela não aparecer, vá no projeto em **Administration** → **Analysis
   Method** e **desligue** a chave "Automatic Analysis"
3. Confira que a chave ficou desligada mesmo depois de recarregar a página

### 5. Pegar o token

Na mesma tela do GitHub Actions o site mostra um token, algo como
`sqp_xxxxxxxx`. **Copie agora**: ele aparece uma vez só.

Se perder, gere outro em **My Account** → **Security** → **Generate Token**.

### 6. Guardar o token no GitHub

1. No repositório, **Settings** → **Secrets and variables** → **Actions**
2. Aba **Secrets**, botão **New repository secret**
3. Name: `SONAR_TOKEN`
4. Secret: o valor copiado
5. **Add secret**

Depois de colado, o GitHub nunca mais mostra o valor, nem para você.

### 7. Conferir

Envie qualquer coisa para a `main`, ou rode o CI pela aba **Actions**. No job
**Backend. Testes e cobertura**, o passo **Análise no SonarQube Cloud** precisa
aparecer como `success`, e não como `skipped`.

O resultado fica em <https://sonarcloud.io/project/overview?id=pamelabaron_TaEmDia>.

## O defeito que estava aqui

O passo existia desde o começo e **nunca rodou**. Em toda execução ele aparecia
como `skipped`, que é verde na tela e não chama atenção.

A condição era `if: env.SONAR_TOKEN != ''`, com o `SONAR_TOKEN` declarado
dentro do próprio passo. A regra do GitHub Actions que pega aqui: a condição
`if` de um passo **não enxerga o `env` declarado nesse mesmo passo**. Ela lê o
`env` do job. Como lá só havia `DATABASE_URL`, `JWT_SECRET` e
`AGENDADOR_ATIVO`, a comparação dava sempre vazio.

Ou seja: configurar o segredo não teria resolvido. A análise continuaria
pulando em silêncio.

A correção foi mover uma linha para o `env` do job, e o
`test_analise_estatica.py` existe para que isso não volte.

## O que esperar da primeira execução

Ela vai apontar dezenas de observações, e isso é normal: é a primeira vez que
alguém olha o projeto inteiro com essa lente.

**Não é preciso corrigir nada.** O playbook do portfólio lista ferramenta de
análise como recomendação ("✅ Preferir"), sem exigir nota nem *quality gate*.
O que vale é a análise rodar e você saber ler o resultado.

Como separar o que importa:

| Categoria | O que é | O que fazer |
|---|---|---|
| **Bugs** | Erro provável de lógica | Ler cada um. Costumam ser poucos e valem a atenção |
| **Vulnerabilities** | Falha de segurança | Ler cada um |
| **Security Hotspots** | Trecho que **merece conferência**, não necessariamente problema | Marcar como revisado depois de olhar |
| **Code Smells** | Estilo, complexidade, duplicação | Ignorar com tranquilidade. É a maior parte |

## As duas marcas de segurança, e por que ficam

A nota de segurança aparece como **E**, por causa de duas marcas graves. As
duas foram investigadas, uma a uma, e **nenhuma é falha**. Elas continuam no
painel porque só quem tem acesso à conta pode marcá-las como alarme falso.

### 1. `armazenamento.py`, "Path Traversal via uploaded file"

O motor vê bytes de um arquivo enviado chegando num `write_bytes` e marca
travessia de caminho. Mas quem está contaminado é o **conteúdo**, não o
caminho. O caminho é formado por três partes, nenhuma delas vinda do usuário:

- `UPLOADS_DIR`, que vem da configuração;
- um `uuid.uuid4()` gerado na hora;
- uma extensão tirada de um dicionário de três valores, cuja chave é o tipo
  **detectado pelos primeiros bytes do arquivo**, não pela extensão enviada.

O nome que a pessoa digitou nunca entra na formação do caminho.

A saída também foi conferida. O download põe o nome original no cabeçalho
`Content-Disposition`, e o Starlette o codifica: um nome contendo `\r\n` sai
como `%0D%0A`, sem injetar cabeçalho nenhum. A rota exige administradora.

Mesmo assim, o nome original passou a ser limpo antes de ser guardado
(`nome_seguro`, no mesmo arquivo): some o caminho, somem os caracteres de
controle, e o tamanho é cortado em 120 preservando a extensão. Não era
necessário para fechar uma brecha; é higiene, e é mais barato agora do que
depois que houver dado de verdade. Tem 19 testes em
`backend/tests/test_nome_do_comprovante.py`.

### 2. `config.py`, "senha de PostgreSQL no código"

A senha apontada é a palavra `troque_esta_senha`, que é um valor de exemplo no
endereço padrão do banco, usado só em desenvolvimento.

E há uma ironia: o sistema **se recusa a subir em produção** com ela. Está em
`validar_para_producao`, no mesmo arquivo, que lista "A senha padrão do banco
continua no DATABASE_URL" entre os problemas que impedem a inicialização. O
Sonar reclama exatamente da proteção que existe contra o problema que ele teme.

### Como marcar as duas no painel

No SonarCloud, abra a marca, clique no menu e escolha **False Positive** (ou
**Won't Fix**, na segunda), colando a justificativa correspondente acima. Feito
isso, a nota de segurança volta para **A**.

Fazer isso é parte do trabalho, não um jeito de esconder: análise estática se
usa lendo cada marca e decidindo. O que não vale é deixar tudo aberto e parar
de olhar.

## Limitação conhecida

A cobertura que chega ao painel é **só a do backend**
(`backend/coverage.xml`). A do frontend é gerada em outro job do CI, e o Sonar
roda dentro do job do backend, que não enxerga o arquivo do outro.

Resolver exigiria um terceiro job que baixa os dois relatórios antes de
analisar. Está anotado como melhoria, não como defeito: a cobertura do
frontend continua conferida pelo próprio Karma, que **falha** o CI abaixo de
25%.
