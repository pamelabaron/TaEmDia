# Monitoramento

Alguém precisa ficar sabendo quando o site cai, e não deve ser a vendedora,
de manhã, pelo cliente que não recebeu a cobrança.

## Como funciona

Um fluxo agendado do GitHub, `.github/workflows/monitor.yml`, consulta o
site a cada 30 minutos:

| Consulta | O que precisa voltar |
|---|---|
| `https://taemdia.duckdns.org/api/health` | resposta 200 **e** `"banco":"ok"` no corpo |
| `https://taemdia.duckdns.org/` | resposta 200 |

Se qualquer uma falhar, o fluxo fica vermelho e **o GitHub manda e-mail**
para a dona do repositório. Não há conta nova em serviço nenhum, nem custo:
o repositório é público.

Antes de acusar, cada consulta tenta três vezes, com 20 segundos entre uma e
outra. Uma oscilação de rede de um segundo não vira alarme.

## Por que o /health pergunta ao banco

Antes, o `/health` respondia "ok" sem olhar nada além de si mesmo. Com o
PostgreSQL parado, a API continuava viva e jurando que estava tudo bem, e o
monitor ficaria verde com o sistema sem conseguir ler nem gravar coisa
nenhuma.

Agora ele faz um `SELECT 1` e responde **503** quando o banco não responde.
Está em `backend/app/main.py`.

## Onde ver

- **Histórico:** aba **Actions** do repositório, fluxo **Monitor**. Cada
  rodada mostra a resposta da API.
- **Rodar agora:** mesmo lugar, botão **Run workflow**.
- **O aviso por e-mail** segue a configuração de notificações da conta no
  GitHub (Settings → Notifications → Actions). O padrão é avisar só quando
  falha, que é o que se quer aqui.

## O que este monitor não cobre

É monitoramento **básico**, e vale dizer o que fica de fora:

- **Não mede lentidão.** Só sabe se respondeu, não se respondeu rápido.
- **Não olha dentro do servidor.** Memória, disco e uso de processador não
  aparecem aqui. Para isso existiria Prometheus com Grafana, que o RFC
  menciona e que não cabe na máquina atual (909 MB de memória).
- **Não confere o WhatsApp.** Se a conexão com o WhatsApp cair, as mensagens
  vão para a fila de reenvio (FE01) e saem quando ela volta, mas o monitor
  não avisa. A tela de Cobranças mostra o que está "Na fila".
- **O GitHub pode atrasar** o agendamento alguns minutos em horário de pico.

Ele também para sozinho se o repositório ficar 60 dias sem nenhuma
atividade: é regra do GitHub para fluxos agendados em repositório público.

## Conferência

`backend/tests/test_monitoramento.py` garante que o `/health` responde 503
com o banco fora do ar, e que o fluxo continua agendado, vigiando os dois
endereços, conferindo o banco no corpo da resposta, insistindo antes de
acusar, e usando `curl -f` (sem ele, até um erro 502 passaria como sucesso).
