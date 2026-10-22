import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

/**
 * Política de Privacidade (LGPD, Lei 13.709/2018).
 *
 * Fica aberta, sem exigir login, porque quem mais precisa dela é justamente
 * quem não tem conta: o cliente do vendedor, que foi cadastrado por outra
 * pessoa e talvez nem saiba que está aqui.
 *
 * O texto parte de uma distinção que a lei faz e que define tudo o mais: quem
 * **decide** usar o dado é o controlador, quem apenas **executa** é o
 * operador. Neste sistema os dois papéis existem ao mesmo tempo, em dados
 * diferentes, e misturá-los seria errado nos dois sentidos: o TáEmDia
 * assumiria responsabilidade por CPF que nunca pediu, e o vendedor ficaria
 * sem a dele sobre dados que ele mesmo coletou.
 */
@Component({
  selector: 'app-privacidade',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="documento">
      <header>
        <a routerLink="/login" class="voltar">Voltar</a>
        <h1>Política de Privacidade</h1>
        <p class="data">Última atualização: 22 de outubro de 2026</p>
      </header>

      <section>
        <h2>Em resumo</h2>
        <p>
          O TáEmDia é um sistema que ajuda pequenos vendedores a controlar
          vendas parceladas e a cobrar pelo WhatsApp. Para isso, ele guarda
          dois conjuntos de dados com donos diferentes: os do vendedor que usa
          o sistema, e os dos clientes que esse vendedor cadastra.
        </p>
        <p>
          A responsabilidade sobre cada conjunto é diferente, e o resto deste
          documento explica como.
        </p>
      </section>

      <section>
        <h2>Quem responde pelo quê</h2>
        <p>
          <strong>Pelos dados do vendedor</strong> (nome, e-mail e foto que
          vêm da conta Google ao entrar) responde o TáEmDia. Foi o sistema que
          pediu esses dados, e é ele que decide o que fazer com eles.
        </p>
        <p>
          <strong>Pelos dados dos clientes</strong> (nome, CPF, telefone,
          endereço, compras e pagamentos) responde o vendedor que os cadastrou.
          Foi ele quem obteve essas informações, na relação comercial dele, e
          quem decidiu registrá-las aqui. O TáEmDia apenas guarda e processa a
          pedido dele.
        </p>
        <p>
          Na linguagem da lei: o TáEmDia é <em>controlador</em> dos dados do
          vendedor e <em>operador</em> dos dados dos clientes dele.
        </p>
      </section>

      <section>
        <h2>Que dados são guardados</h2>
        <h3>Do vendedor</h3>
        <ul>
          <li>Nome, endereço de e-mail e foto do perfil, fornecidos pela conta
              Google no momento da entrada</li>
          <li>Configurações de uso: horários de envio, textos das mensagens,
              número de WhatsApp que envia as cobranças</li>
          <li>Comprovantes de pagamento da assinatura, quando enviados</li>
        </ul>
        <h3>Dos clientes do vendedor</h3>
        <ul>
          <li>Nome e número de WhatsApp, que são obrigatórios</li>
          <li>CPF e endereço, que são opcionais</li>
          <li>Vendas, parcelas, vencimentos e pagamentos registrados</li>
          <li>Mensagens enviadas pelo sistema e as respostas recebidas</li>
        </ul>
        <p>
          O sistema <strong>não</strong> guarda senha de ninguém: a entrada é
          feita pela conta Google, e a senha fica com o Google.
        </p>
      </section>

      <section>
        <h2>Para que servem</h2>
        <p>
          Os dados existem para executar o que o vendedor contratou: calcular
          parcelas e vencimentos, enviar as cobranças nas datas certas,
          registrar o que foi pago, e mostrar os relatórios dessa atividade.
          Nenhum dado é usado para outra finalidade.
        </p>
        <p>
          <strong>Nada é vendido, cedido ou compartilhado</strong> com
          terceiros para fins comerciais, de publicidade ou de análise.
        </p>
      </section>

      <section>
        <h2>Quem mais tem acesso</h2>
        <p>
          Três serviços participam do funcionamento, cada um com uma parte:
        </p>
        <ul>
          <li><strong>Google</strong>, que faz a entrada no sistema. Recebe
              apenas o pedido de autenticação e devolve nome, e-mail e foto</li>
          <li><strong>Amazon Web Services</strong>, onde o sistema roda e os
              dados ficam armazenados, em servidor no exterior</li>
          <li><strong>WhatsApp</strong>, por onde as mensagens de cobrança são
              enviadas. Recebe o número do destinatário e o texto da
              mensagem</li>
        </ul>
        <p>
          Cada conta enxerga apenas os próprios clientes. Um vendedor nunca vê
          os dados de outro.
        </p>
      </section>

      <section>
        <h2>Por quanto tempo ficam</h2>
        <p>
          Enquanto a conta existir. Ao pedir a exclusão da conta, os dados são
          apagados em até 30 dias, com uma exceção: registros que a lei obrigue
          a manter, como comprovantes relacionados a pagamentos, permanecem
          pelo prazo legal.
        </p>
      </section>

      <section>
        <h2>Seus direitos</h2>
        <p>A LGPD garante a qualquer pessoa o direito de:</p>
        <ul>
          <li>saber se há dados seus no sistema, e quais são</li>
          <li>pedir correção de dado errado ou desatualizado</li>
          <li>pedir a exclusão dos seus dados</li>
          <li>pedir uma cópia, em formato que dê para levar para outro lugar</li>
          <li>saber com quem os dados foram compartilhados</li>
          <li>revogar o consentimento dado antes</li>
        </ul>
        <p>
          Para exercer qualquer um deles, escreva para
          <a href="mailto:taemdia.contato&#64;gmail.com">taemdia.contato&#64;gmail.com</a>.
          O pedido é respondido em até 15 dias.
        </p>
        <p class="nota">
          Se você é cliente de um vendedor que usa o TáEmDia e quer sair da
          lista dele, pode escrever para nós, mas o caminho mais rápido é
          pedir direto a ele: é ele quem decide sobre esses dados, e quem pode
          apagá-los na hora.
        </p>
      </section>

      <section>
        <h2>Segurança</h2>
        <ul>
          <li>Todo o acesso ao site acontece por conexão cifrada (HTTPS)</li>
          <li>A entrada é feita pelo Google, sem senha guardada aqui</li>
          <li>Cada consulta ao banco filtra pela conta de quem pergunta, de
              modo que um vendedor não alcança dados de outro</li>
          <li>Os comprovantes enviados ficam fora de qualquer pasta pública</li>
        </ul>
        <p>
          Nenhum sistema é imune a falhas. Em caso de incidente que possa
          trazer risco às pessoas, os afetados e a Autoridade Nacional de
          Proteção de Dados são comunicados.
        </p>
      </section>

      <section>
        <h2>Sobre o projeto</h2>
        <p>
          O TáEmDia é um trabalho de conclusão de curso de Engenharia de
          Software da Católica de Santa Catarina, em operação real. Isso não
          reduz nenhuma das obrigações descritas aqui, mas significa que não
          há empresa por trás dele: não há garantia de disponibilidade nem
          compromisso de continuidade depois do período acadêmico.
        </p>
        <p>
          Se o sistema for encerrado, os usuários serão avisados com
          antecedência de pelo menos 30 dias para levarem seus dados.
        </p>
      </section>

      <section>
        <h2>Mudanças neste documento</h2>
        <p>
          Alterações relevantes são avisadas dentro do sistema. A data no topo
          mostra a última versão.
        </p>
      </section>

      <footer>
        <a routerLink="/termos">Termos de Uso</a>
        <a routerLink="/login">Voltar ao início</a>
      </footer>
    </div>
  `,
  styleUrl: './documento.scss',
})
export class PrivacidadeComponent {}
