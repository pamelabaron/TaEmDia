# Guia de Instalação do Ambiente — TáEmDia (Windows 11, 64 bits, Intel)

> **Regra de ouro:** em toda página de download, escolha **Windows · 64-bit (x64 / AMD64)**.
> "AMD64" é só o nome do padrão 64 bits — serve para processadores Intel também.
> Nunca escolha 32-bit nem ARM64.

Já instalado nesta máquina: **Git** e **VS Code** (não precisa reinstalar).

Instale **nesta ordem**. Marque cada caixa ao concluir.

---

## [ ] Passo 1 — WSL 2 (base do Docker)
1. Clique no menu Iniciar, digite **PowerShell**, clique com o botão direito em
   **Windows PowerShell** → **Executar como administrador**.
2. Na janela azul, digite e tecle Enter:
   ```
   wsl --install
   ```
3. Espere terminar e **reinicie o computador** quando ele pedir.

**Como saber que deu certo:** após reiniciar, abra o PowerShell e digite `wsl --status`.
Deve aparecer uma versão, sem erro de "não está instalado".

---

## [ ] Passo 2 — Docker Desktop
1. Acesse **https://www.docker.com/products/docker-desktop/**
2. Clique em **Download for Windows – AMD64**.
3. Abra o instalador. Mantenha marcada a opção **"Use WSL 2 instead of Hyper-V"**.
4. Conclua e, se pedir, reinicie.
5. Abra o **Docker Desktop** pelo menu Iniciar e espere a **baleia ficar verde**
   ("Engine running" no rodapé).

**Como saber que deu certo:** no PowerShell, `docker --version` mostra um número de versão.

---

## [ ] Passo 3 — Python 3.12
1. Acesse **https://www.python.org/downloads/windows/**
2. Baixe **"Windows installer (64-bit)"** da versão **3.12.x** (a mais recente 3.12,
   **não** a 3.13).
3. Abra o instalador e, **na primeira tela**, marque a caixa
   **"Add python.exe to PATH"** (muito importante!). Depois clique em **Install Now**.

**Como saber que deu certo:** no PowerShell, `python --version` mostra `Python 3.12.x`.

---

## [ ] Passo 4 — Node.js 20 LTS (para o Angular)
1. Acesse **https://nodejs.org**
2. Baixe o botão **LTS** (deve dizer "20.x.x LTS") — **Windows Installer (.msi) 64-bit**.
3. Instale com as opções padrão (pode clicar "Next" até o fim).

**Como saber que deu certo:** no PowerShell, `node --version` mostra `v20.x.x`.

---

## Depois de tudo instalado
Volte e avise. Eu rodo **uma verificação única** que confere Git, Docker, Python e Node
de uma vez, e então:
1. Gero o app **Angular** de verdade.
2. Crio a **primeira migration** do banco (tabelas vendedor e cliente).
3. Subimos o sistema com `docker compose up` e você vê a API no ar em
   http://localhost:8000/docs
