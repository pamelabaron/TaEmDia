# Como criar as credenciais do Login com Google (Google Cloud)

O sistema usa o **Login com Google** (OAuth 2.0). Para funcionar, você precisa criar uma
"credencial" gratuita no Google Cloud e colar dois valores no arquivo `.env`.
É uma vez só. Siga os passos.

> Tudo aqui é **gratuito**. Não precisa cartão de crédito.

---

## Passo 1 — Criar um projeto
1. Acesse **https://console.cloud.google.com/**
2. Faça login com sua conta Google.
3. No topo, clique no seletor de projeto → **"Novo projeto"**.
4. Nome: `TaEmDia` → **Criar**. Espere criar e selecione esse projeto.

## Passo 2 — Configurar a tela de consentimento
1. No menu (☰) → **APIs e serviços** → **Tela de permissão OAuth**
   (em inglês: *OAuth consent screen*).
2. Tipo de usuário: **Externo** → **Criar**.
3. Preencha só o obrigatório:
   - Nome do app: `TáEmDia`
   - E-mail de suporte: seu e-mail
   - E-mail do desenvolvedor: seu e-mail
4. **Salvar e continuar** nas telas seguintes (Escopos, etc.) sem adicionar nada.
5. Na etapa **Usuários de teste**, clique **+ Add users** e adicione o **seu próprio
   e-mail Google** (enquanto o app está em modo de teste, só e-mails dessa lista conseguem entrar).
6. **Salvar**.

## Passo 3 — Criar a credencial (Client ID)
1. Menu → **APIs e serviços** → **Credenciais**.
2. **+ Criar credenciais** → **ID do cliente OAuth**.
3. Tipo de aplicativo: **Aplicativo da Web**.
4. Nome: `TaEmDia Web`.
5. Em **URIs de redirecionamento autorizados**, clique **+ Adicionar URI** e cole
   exatamente:
   ```
   http://localhost:8000/auth/google/callback
   ```
6. **Criar**.
7. Aparece uma janela com **ID do cliente** e **Chave secreta do cliente**.
   **Copie os dois** (dá pra copiar depois também, na lista de credenciais).

## Passo 4 — Colar no arquivo .env
Abra o arquivo `.env` na pasta do projeto e preencha:
```
GOOGLE_CLIENT_ID=cole_aqui_o_id_do_cliente
GOOGLE_CLIENT_SECRET=cole_aqui_a_chave_secreta
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```
Salve o arquivo.

## Passo 5 — Reiniciar e testar
No terminal, na pasta do projeto:
```
docker compose restart backend
```
Depois, abra no navegador:
```
http://localhost:8000/auth/google/login
```
Você deve ser levada à tela do Google, escolher sua conta e, ao final, o sistema
devolve um **token** (JWT). Isso confirma que o login está funcionando. 🎉

> Quando o **frontend Angular** existir, esse fluxo acontecerá pelo botão
> "Continuar com Google" na tela de login, sem você ver o token.

---

### Dúvidas comuns
- **"Acesso bloqueado / app não verificado":** normal em modo de teste. Verifique se
  seu e-mail está em *Usuários de teste* (Passo 2.5) e clique em "Avançado → Acessar
  (não seguro)". Como o app é seu, é seguro.
- **"redirect_uri_mismatch":** o endereço no Passo 3.5 tem que ser **idêntico** ao do
  `.env` (mesmas letras, mesma porta 8000, sem barra no final).
