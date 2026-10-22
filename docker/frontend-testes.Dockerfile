# Imagem só para rodar os testes do frontend.
#
# O node:20 não traz navegador, e o Karma precisa de um para executar o
# código. Instalar o Chromium aqui deixa o teste reprodutível: roda igual no
# computador da autora e no CI, sem ninguém instalar nada no sistema.
FROM node:20-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# O Karma procura o navegador por esta variável.
ENV CHROME_BIN=/usr/bin/chromium

WORKDIR /app
