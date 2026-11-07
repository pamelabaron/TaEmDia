import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

/**
 * Termos de Uso.
 *
 * Aberto sem login, pelo mesmo motivo da Política de Privacidade: quem decide
 * se vai usar o sistema precisa ler as condições antes de criar a conta, não
 * depois.
 *
 * O ponto mais importante do texto é a obrigação que o vendedor assume ao
 * cadastrar terceiros. O sistema guarda CPF e telefone de pessoas que nunca
 * entraram aqui, e quem respondeu por obter esses dados foi ele. Dizer isso
 * com todas as letras protege as duas partes: o vendedor sabe o que está
 * assumindo, e a autora não responde por dado que nunca pediu.
 */
@Component({
  selector: 'app-termos',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="documento">
      <header>
        <a routerLink="/login" class="voltar">Voltar</a>
        <h1>Termos de Uso</h1>
        <p class="data">Última atualização: 22 de outubro de 2026</p>
      </header>

      <section>
        <h2>O que é o TáEmDia</h2>
        <p>
          Um sistema para pequenos vendedores controlarem vendas parceladas e
          cobrarem pelo WhatsApp de forma automática. Ele registra clientes,
          calcula parcelas e vencimentos, envia as mensagens nas datas certas
          e acompanha o que foi pago.
        </p>
        <p>
          Ao criar uma conta, você concorda com estes termos. Se não concordar
          com algum ponto, não use o sistema.
        </p>
      </section>

      <section>
        <h2>Conta</h2>
        <ul>
          <li>A entrada é feita pela conta Google. Não existe senha própria do
              TáEmDia, e por isso cuidar da sua conta Google é cuidar do
              acesso ao sistema</li>
          <li>Cada conta enxerga apenas os próprios clientes</li>
          <li>Você é responsável pelo que acontece na sua conta</li>
          <li>Você pode pedir o encerramento a qualquer momento, sem multa nem
              aviso prévio</li>
        </ul>
      </section>

      <section>
        <h2>O que você assume ao cadastrar um cliente</h2>
        <p>
          Esta é a parte mais importante destes termos, porque envolve pessoas
          que não estão nesta conversa.
        </p>
        <p>
          Ao cadastrar alguém, você declara que obteve os dados dessa pessoa
          de forma legítima, na sua relação comercial com ela, e que pode
          usá-los para cobrar o que ela deve. <strong>A responsabilidade sobre
          esses dados é sua</strong>: foi você quem os coletou e quem decidiu
          registrá-los aqui.
        </p>
        <p>Em particular, você se compromete a:</p>
        <ul>
          <li>cadastrar apenas pessoas com quem tem relação comercial de
              verdade</li>
          <li>manter os dados corretos e atualizados</li>
          <li>atender quem pedir correção ou exclusão dos próprios dados</li>
          <li>não usar o sistema para constranger, ameaçar ou expor ninguém</li>
        </ul>
        <p class="nota">
          Cobrar é um direito. Constranger não é. O Código de Defesa do
          Consumidor proíbe expor o devedor ao ridículo ou submetê-lo a
          ameaça. O sistema ajuda nisso ao limitar o horário de envio e a
          quantidade de mensagens por dia, mas o texto que sai é escrito por
          você.
        </p>
      </section>

      <section>
        <h2>Como as mensagens são enviadas</h2>
        <ul>
          <li>As cobranças saem apenas em horário comercial, das 8h às 20h</li>
          <li>Há limite diário de mensagens por cliente</li>
          <li>As mensagens saem do número de WhatsApp que você conectou, e
              aparecem para o cliente como vindas de você</li>
          <li>Você pode desligar o envio automático a qualquer momento, por
              cliente ou para todos</li>
        </ul>
        <p>
          O TáEmDia depende do WhatsApp para entregar as mensagens e não
          controla esse serviço. Bloqueio, instabilidade ou mudança de regras
          por parte dele podem afetar o envio.
        </p>
      </section>

      <section>
        <h2>Pagamento confirmado por você</h2>
        <p>
          Quando um cliente responde que já pagou, o sistema marca a parcela
          como aguardando conferência e <strong>não</strong> dá baixa sozinho.
          Só você confirma o recebimento. O sistema não movimenta dinheiro,
          não recebe pagamento de cliente e não serve de intermediário
          financeiro entre vocês.
        </p>
      </section>

      <section>
        <h2>Assinatura</h2>
        <ul>
          <li>Novas contas começam com um período de teste gratuito</li>
          <li>Depois dele, o uso depende de assinatura ativa</li>
          <li>O pagamento é feito por Pix, e o comprovante é enviado pelo
              sistema para conferência manual</li>
          <li>Com a assinatura vencida, você continua <strong>vendo</strong>
              tudo: clientes, parcelas e relatórios. O que fica suspenso é
              cadastrar, cobrar e conectar o WhatsApp</li>
          <li>Não há cobrança automática nem renovação sem você pagar</li>
        </ul>
      </section>

      <section>
        <h2>O que não é permitido</h2>
        <ul>
          <li>Cadastrar pessoas com quem você não tem relação comercial</li>
          <li>Usar o sistema para enviar propaganda ou mensagem em massa</li>
          <li>Tentar acessar dados de outra conta</li>
          <li>Qualquer uso que viole a lei</li>
        </ul>
        <p>
          Contas que descumprirem estes pontos podem ser suspensas.
        </p>
      </section>

      <section>
        <h2>Limites do serviço</h2>
        <p>
          O TáEmDia é um trabalho de conclusão de curso de Engenharia de
          Software da Católica de Santa Catarina, em operação real. Ele é
          oferecido no estado em que se encontra, sem garantia de
          disponibilidade contínua e sem compromisso de continuidade depois do
          período acadêmico.
        </p>
        <p>
          A autora não responde por prejuízo decorrente de mensagem não
          entregue, sistema fora do ar ou perda de dado por falha de serviço
          de terceiro. <strong>Mantenha o seu próprio controle do que é
          importante</strong>, em paralelo.
        </p>
        <p>
          Se o sistema for encerrado, os usuários serão avisados com pelo
          menos 30 dias de antecedência para levarem seus dados.
        </p>
      </section>

      <section>
        <h2>Privacidade</h2>
        <p>
          O tratamento dos dados está descrito na
          <a routerLink="/privacidade">Política de Privacidade</a>, que faz
          parte destes termos.
        </p>
      </section>

      <section>
        <h2>Mudanças e contato</h2>
        <p>
          Alterações relevantes nestes termos são avisadas dentro do sistema.
          Para qualquer dúvida, escreva para
          <a href="mailto:taemdia.contato&#64;gmail.com">taemdia.contato&#64;gmail.com</a>.
        </p>
        <p>
          Aplica-se a lei brasileira, e fica eleito o foro da comarca de
          Joinville, Santa Catarina.
        </p>
      </section>

      <footer>
        <a routerLink="/privacidade">Política de Privacidade</a>
        <a routerLink="/login">Voltar ao início</a>
      </footer>
    </div>
  `,
  styleUrl: './documento.scss',
})
export class TermosComponent {}
