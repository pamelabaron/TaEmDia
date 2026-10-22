import { AfterViewInit, Component, OnDestroy, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';

interface Recurso { titulo: string; texto: string; }
interface Passo { numero: string; titulo: string; texto: string; }

const RECURSOS: Recurso[] = [
  {
    titulo: 'Carteira de clientes',
    texto: 'Cadastro completo com histórico de compras, pagamentos e o saldo devedor de cada pessoa sempre à mão.',
  },
  {
    titulo: 'Cobrança automática',
    texto: 'O sistema envia a mensagem no WhatsApp na data certa: lembrete antes, aviso no vencimento e cobrança no atraso.',
  },
  {
    titulo: 'Mensagens do seu jeito',
    texto: 'Modelos personalizáveis que preenchem sozinhos o nome, o valor e a data. Você escreve uma vez e o sistema usa sempre.',
  },
  {
    titulo: 'Painel financeiro',
    texto: 'Quanto você tem a receber, quanto já recebeu no mês e quanto está em atraso, tudo em uma tela só.',
  },
  {
    titulo: 'Ranking de pagadores',
    texto: 'O sistema classifica quem paga em dia e quem costuma atrasar, com base no histórico real de cada cliente.',
  },
  {
    titulo: 'Resumo diário',
    texto: 'No fim do dia você recebe no WhatsApp um resumo do que foi cobrado, quem pagou e quem respondeu.',
  },
];

const PASSOS: Passo[] = [
  { numero: '1', titulo: 'Cadastre o cliente', texto: 'Nome e WhatsApp bastam. Leva menos de um minuto.' },
  { numero: '2', titulo: 'Registre a venda', texto: 'Informe o valor e em quantas vezes. O sistema calcula todos os vencimentos.' },
  { numero: '3', titulo: 'Deixe cobrar sozinho', texto: 'Na data certa, a mensagem sai no WhatsApp do cliente. Você não precisa lembrar.' },
  { numero: '4', titulo: 'Confirme o pagamento', texto: 'Quando o dinheiro cair, um clique dá baixa e atualiza saldo, painel e ranking.' },
];

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [MatButtonModule, MatIconModule, RouterLink],
  template: `
    <div class="pagina">

      <header class="topo">
        <span class="marca"><mat-icon>task_alt</mat-icon> TáEmDia</span>
        <button mat-flat-button color="primary" (click)="entrar()">Entrar</button>
      </header>

      <section class="capa">
        <!-- As luzes que se deslocam atrás da capa. Puramente decorativas,
             por isso escondidas de leitor de tela. Ficam no documento, e não
             num pseudo-elemento, porque cada uma precisa de um movimento
             próprio: três camadas num elemento só só poderiam se mover
             juntas, e movimento igual lê como um bloco deslizando. -->
        <div class="luzes" aria-hidden="true">
          <span class="luz luz-a"></span>
          <span class="luz luz-b"></span>
          <span class="luz luz-c"></span>
        </div>

        <div class="capa-texto">
          <h1>Suas cobranças <span class="destaque">em dia</span>, sem você precisar lembrar.</h1>
          <p class="subtitulo">
            O TáEmDia organiza seus clientes, controla as parcelas e envia as cobranças
            pelo WhatsApp automaticamente, para você parar de cobrar um por um.
          </p>
          <button mat-flat-button color="primary" class="btn-grande" (click)="entrar()">
            <mat-icon>login</mat-icon> Continuar com Google
          </button>
          <p class="aviso">Entrada pela sua conta Google. Você não cria nem memoriza senha.</p>
        </div>

        <!-- O único momento encenado da página. A conversa acontece sozinha
             ao abrir: a cobrança chega, o cliente responde, a etiqueta muda.
             É a promessa do produto representada, não enfeite.

             Cada peça entra com um atraso próprio, imitando o ritmo de uma
             conversa de verdade. A resposta do cliente demora mais que a
             cobrança, porque gente demora. -->
        <div class="capa-visual" aria-hidden="true">
          <div class="celular">
            <div class="celular-topo"><span class="bolinha"></span> Cliente</div>
            <div class="balao recebido entra" style="--atraso: 0.5s">
              Olá Rosangela! Passando para lembrar que sua parcela de
              <strong>R$ 100,00</strong> vence em <strong>10/09</strong>.
              <div class="opcoes">1 - Já paguei<br>2 - Vou pagar hoje<br>3 - Não consigo pagar</div>
            </div>
            <div class="digitando entra" style="--atraso: 1.6s">
              <span></span><span></span><span></span>
            </div>
            <div class="balao enviado entra" style="--atraso: 2.9s">1</div>
            <div class="etiqueta-status entra" style="--atraso: 3.5s">
              <mat-icon>schedule</mat-icon> Aguardando sua confirmação
            </div>
          </div>
        </div>
      </section>

      <section class="faixa problema com-grao">
        <h2>Cobrar manualmente custa caro</h2>
        <p class="secao-texto">
          Em pesquisa com pequenos empreendedores que vendem parcelado, o retrato foi este:
        </p>
        <dl class="numeros">
          <div class="numero">
            <dt>100%</dt>
            <dd>vendem parcelado e precisam controlar vencimentos</dd>
          </div>
          <div class="numero">
            <dt>83%</dt>
            <dd>cobram manualmente, uma mensagem de cada vez</dd>
          </div>
          <div class="numero">
            <dt>50%</dt>
            <dd>têm dificuldade de cobrar sem parecer insistente</dd>
          </div>
        </dl>
      </section>

      <section class="faixa">
        <h2>Do cadastro à baixa, em quatro passos</h2>
        <p class="secao-texto">Quatro passos, e o sistema assume a parte repetitiva.</p>
        <div class="passos">
          @for (p of passos; track p.numero) {
            <div class="passo">
              <span class="passo-numero">{{ p.numero }}</span>
              <h3>{{ p.titulo }}</h3>
              <p>{{ p.texto }}</p>
            </div>
          }
        </div>
      </section>

      <section class="faixa claro">
        <h2>Seis coisas que você deixa de fazer à mão</h2>
        <p class="secao-texto">Cada uma delas tomava um pedaço do seu dia.</p>
        <ul class="recursos">
          @for (r of recursos; track r.titulo) {
            <li class="recurso">
              <h3>{{ r.titulo }}</h3>
              <p>{{ r.texto }}</p>
            </li>
          }
        </ul>
      </section>

      <section class="faixa">
        <h2>O que ele nunca faz sem você</h2>
        <div class="garantias">
          <div class="garantia">
            <mat-icon>fact_check</mat-icon>
            <div>
              <h3>Você decide o que é pago</h3>
              <p>Se o cliente responder "já paguei", a parcela fica aguardando sua conferência. Só você dá baixa.</p>
            </div>
          </div>
          <div class="garantia">
            <mat-icon>do_not_disturb_on</mat-icon>
            <div>
              <h3>Sem incomodar fora de hora</h3>
              <p>As mensagens saem apenas em horário comercial, com limite diário por cliente.</p>
            </div>
          </div>
          <div class="garantia">
            <mat-icon>visibility_off</mat-icon>
            <div>
              <h3>Seus dados são só seus</h3>
              <p>Entrada pela conta Google, sem senha guardada, e cada conta enxerga apenas os próprios clientes.</p>
            </div>
          </div>
        </div>
      </section>

      <section class="chamada com-grao">
        <h2>Pare de cobrar um por um</h2>
        <p>Leva menos de um minuto para cadastrar o primeiro cliente.</p>
        <button mat-flat-button class="btn-grande botao-claro" (click)="entrar()">
          <mat-icon>login</mat-icon> Continuar com Google
        </button>
      </section>

      <footer class="rodape">
        <span><strong>TáEmDia</strong> · Cobrança automatizada via WhatsApp</span>
        <nav class="rodape-links">
          <a routerLink="/privacidade">Privacidade</a>
          <a routerLink="/termos">Termos de uso</a>
        </nav>
        <span class="rodape-fraco">© {{ ano }} TáEmDia</span>
      </footer>
    </div>
  `,
  styles: [`
    /* A aurora da capa sangra para fora do container de propósito, e sem um
       recorte aqui ela alargava o documento: a página rolava para os lados.
       O recorte é "clip", não "hidden": "hidden" transformaria este elemento
       numa área de rolagem própria e o cabeçalho fixo (.topo, sticky) deixaria
       de grudar no topo. */
    .pagina { background: var(--superficie); overflow-x: clip; }

    /* Navegador sem "overflow: clip" (Safari anterior ao 16): a aurora não
       sangra para os lados, para não haver o que recortar. */
    @supports not (overflow: clip) {
      .capa::before { left: 0; right: 0; }
    }
    h1, h2, h3 { color: var(--texto); }

    /* topo fixo */
    .topo {
      position: sticky; top: 0; z-index: 10;
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 28px;
      background: rgba(20, 15, 26, 0.86);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--borda);
    }
    .marca {
      display: flex; align-items: center; gap: 8px;
      font-weight: 600; font-size: 1.15rem; color: var(--lilas-300);
    }

    /* apresentação */
    .capa {
      position: relative;
      display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 48px; align-items: center;
      padding: 84px 28px 104px; max-width: 1100px; margin: 0 auto;
    }
    /* Aurora atrás da capa, agora em movimento.
       Sangra para fora do container de propósito: luz contida numa caixa
       parece adesivo.

       Cada luz é um círculo desfocado que se desloca no seu próprio ritmo,
       com duração e atraso diferentes dos vizinhos. Durações que não são
       múltiplas entre si é o que impede o conjunto de voltar ao mesmo arranjo
       e virar um laço visível: as três só se repetiriam juntas depois de
       muitos minutos.

       O movimento é lento de propósito, na casa dos 20 segundos. Luz de fundo
       que se percebe mexendo disputa com o texto; o que se quer é a sensação
       de que a tela respira. */
    /* O seletor é .capa > .luzes, e não só .luzes, de propósito. A regra
       ".capa > *" mais abaixo põe position: relative em todo filho direto,
       tem a mesma especificidade e vem depois: com o seletor curto, ela
       vencia, as luzes voltavam para o fluxo e ocupavam uma coluna da grade,
       empurrando o texto da capa para o lado. */
    .capa > .luzes {
      position: absolute; inset: -10% -30% -20% -30%;
      pointer-events: none; z-index: 0;
      overflow: hidden;
    }
    .luz {
      position: absolute; display: block;
      border-radius: 50%;
      /* O desfoque é o que transforma o círculo em luz. Sem ele, é uma bola
         roxa no fundo da página. */
      filter: blur(70px);
      /* Avisa o navegador para preparar a camada antes de o movimento
         começar, em vez de recalcular a cada quadro. */
      will-change: transform;
    }
    /* A primeira versão percorria 7% da própria largura: 42 pixels numa forma
       de 608. Medido, andava; olhado, não. Agora cada luz percorre perto de
       um sexto do próprio tamanho, e cada uma num eixo diferente, para o
       conjunto não parecer um bloco escorregando. */
    .luz-a {
      width: 34rem; height: 24rem; left: 4%; top: 6%;
      background: rgba(201, 169, 255, 0.40);
      animation: deriva-a 23s ease-in-out infinite alternate;
    }
    .luz-b {
      width: 30rem; height: 22rem; left: 58%; top: -4%;
      background: rgba(134, 99, 187, 0.34);
      animation: deriva-b 31s ease-in-out infinite alternate;
    }
    .luz-c {
      width: 26rem; height: 20rem; left: 72%; top: 62%;
      background: rgba(93, 64, 128, 0.30);
      animation: deriva-c 37s ease-in-out infinite alternate;
    }

    /* Só transform e opacity: são as duas propriedades que o navegador anima
       sem recalcular o layout da página a cada quadro. Animar largura ou
       posição aqui travaria a rolagem em celular. */
    /* Uma puxa para a direita e desce, outra atravessa para a esquerda, a
       terceira sobe. Direções distintas são o que faz o fundo parecer vivo
       em vez de deslizar inteiro. */
    @keyframes deriva-a {
      from { transform: translate3d(0, 0, 0) scale(1); }
      to   { transform: translate3d(19%, 14%, 0) scale(1.2); }
    }
    @keyframes deriva-b {
      from { transform: translate3d(0, 0, 0) scale(1.12); }
      to   { transform: translate3d(-22%, 11%, 0) scale(0.88); }
    }
    @keyframes deriva-c {
      from { transform: translate3d(0, 0, 0) scale(0.92); }
      to   { transform: translate3d(-14%, -24%, 0) scale(1.18); }
    }

    /* Quem pediu menos movimento no sistema vê as luzes paradas, na posição
       inicial. A página não perde nada: a aurora continua lá, só não anda. */
    @media (prefers-reduced-motion: reduce) {
      .luz { animation: none; }
    }
    .capa > * { position: relative; z-index: 1; }
    .selo {
      display: inline-block; background: rgba(201, 169, 255, 0.14); color: var(--lilas-300);
      padding: 6px 14px; border-radius: 999px; font-size: 0.8rem; font-weight: 600;
      margin-bottom: 18px;
    }
    /* O título estava em 2.7rem, tamanho de subtítulo. Numa página que existe
       para convencer, o título é o elemento; cresce até caber na largura e
       fecha o espacejamento, que é o que faz texto grande parecer desenhado em
       vez de apenas ampliado. */
    .capa h1 {
      font-size: clamp(2.6rem, 5.2vw, 4.4rem);
      line-height: 0.98;
      margin: 0 0 22px;
      letter-spacing: -0.038em;
      font-weight: 700;
    }

    /* O único momento autorado de movimento do site, na primeira dobra. As
       demais seções entram sem animação: repetir a mesma entrada em tudo é o
       que faz um site parecer um modelo preenchido. */
    .capa-texto > *, .capa-visual { animation: entrar 700ms cubic-bezier(0.16, 1, 0.3, 1) both; }
    .capa-texto > *:nth-child(1) { animation-delay: 40ms; }
    .capa-texto > *:nth-child(2) { animation-delay: 110ms; }
    .capa-texto > *:nth-child(3) { animation-delay: 180ms; }
    .capa-texto > *:nth-child(4) { animation-delay: 240ms; }
    .capa-visual { animation-delay: 200ms; }
    @keyframes entrar {
      from { opacity: 0; transform: translateY(14px); filter: blur(6px); }
      to   { opacity: 1; transform: none; filter: none; }
    }
    @media (prefers-reduced-motion: reduce) {
      .capa-texto > *, .capa-visual { animation: none; }
    }
    /* Sem traço atrás: o destaque é a própria cor, no verde mais saturado da
       paleta, que já se separa do texto escuro em volta. */
    // Lilás, não ameixa: a ameixa média sobre o fundo escuro dava 2,9 de
    // contraste, abaixo do mínimo de 3 para texto grande.
    .destaque { color: var(--lilas-400); }
    .subtitulo { font-size: 1.1rem; color: var(--texto-suave); line-height: 1.6; margin: 0 0 28px; max-width: 30em; }
    .btn-grande { height: 50px; padding: 0 28px !important; font-size: 1rem; }
    .btn-grande mat-icon { margin-right: 8px; }
    .aviso { font-size: 0.82rem; color: var(--texto-fraco); margin-top: 14px; }

    /* ilustração da conversa */
    .capa-visual { display: flex; justify-content: center; }
    .celular {
      position: relative;
      width: 300px; background: var(--superficie-2); border: 1px solid rgba(201, 169, 255, 0.16);
      border-radius: 22px; padding: 16px;
      /* Sombra em camadas: contato curto e escuro perto do objeto, difusa e
         clara longe. Uma sombra só, grande e uniforme, boia. */
      box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.08),
        0 1px 2px rgba(39, 26, 56, 0.10),
        0 8px 16px -6px rgba(39, 26, 56, 0.14),
        0 28px 56px -20px rgba(39, 26, 56, 0.28);
    }
    /* Reflexo no vidro: uma faixa clara na diagonal do canto superior. */
    .celular::after {
      content: ""; position: absolute; inset: 0; border-radius: 22px;
      pointer-events: none;
      background: linear-gradient(152deg, rgba(255, 255, 255, 0.07) 0%,
                                  rgba(255, 255, 255, 0) 38%);
    }
    .celular > * { position: relative; z-index: 1; }

    /* A encenação da conversa.
       Começa invisível e deslocada, e chega no lugar com desaceleração: a
       curva é a mesma do resto do sistema, para o movimento parecer da mesma
       mão. "backwards" mantém a peça invisível durante o atraso; sem isso
       ela pisca na tela antes de a animação começar. */
    .entra {
      /* "both", e não "backwards": o primeiro mantém a peça escondida durante
         a espera E preserva o estado final depois. Só com "backwards" o
         elemento volta ao que era quando a animação acaba, e a conversa
         inteira terminava invisível.

         A opacidade base fica em 1, não em 0: se as animações não rodarem,
         por navegador antigo ou falha qualquer, o conteúdo aparece. Página
         que depende de animação para ser lida é página que some sozinha. */
      animation: chega 520ms cubic-bezier(0.16, 1, 0.3, 1) var(--atraso, 0s) both;
    }
    .balao.recebido.entra { animation-name: chega-da-esquerda; }
    .balao.enviado.entra { animation-name: chega-da-direita; }

    @keyframes chega {
      from { opacity: 0; transform: translateY(10px); }
      to   { opacity: 1; transform: none; }
    }
    /* Os balões entram do lado de quem fala, como numa conversa de verdade:
       o do cliente da esquerda, a resposta da direita. */
    @keyframes chega-da-esquerda {
      from { opacity: 0; transform: translate3d(-14px, 8px, 0) scale(0.96); }
      to   { opacity: 1; transform: none; }
    }
    @keyframes chega-da-direita {
      from { opacity: 0; transform: translate3d(14px, 8px, 0) scale(0.96); }
      to   { opacity: 1; transform: none; }
    }

    /* Os três pontinhos de "digitando". Existem por um motivo de ritmo: sem
       eles, a resposta do cliente aparece do nada e a cena fica mecânica.
       Com eles, há uma pausa que se lê como alguém pensando.
       Somem quando a resposta chega. */
    .digitando {
      display: flex; gap: 4px; align-items: center;
      align-self: flex-end;
      padding: 10px 14px; border-radius: 14px; border-bottom-right-radius: 4px;
      background: rgba(201, 169, 255, 0.12);
      width: fit-content; margin-left: auto;
      /* Dois tempos na mesma peça: entra, e some quando a resposta chega.
         O primeiro é "both" pelo mesmo motivo do resto; o segundo é
         "forwards" para o desaparecimento ficar. */
      animation: chega 400ms ease-out var(--atraso, 0s) both,
                 some 300ms ease-in 2.9s forwards;
    }
    .digitando span {
      width: 6px; height: 6px; border-radius: 50%;
      background: var(--lilas-300); opacity: 0.5;
      animation: pulsa 1.2s ease-in-out infinite;
    }
    .digitando span:nth-child(2) { animation-delay: 0.18s; }
    .digitando span:nth-child(3) { animation-delay: 0.36s; }

    @keyframes pulsa {
      0%, 60%, 100% { opacity: 0.35; transform: translateY(0); }
      30%           { opacity: 1;    transform: translateY(-3px); }
    }
    @keyframes some {
      to { opacity: 0; height: 0; padding: 0; margin: 0; overflow: hidden; }
    }

    /* Com menos movimento pedido, a conversa aparece inteira e parada. O
       conteúdo é o mesmo; o que se perde é só a encenação. */
    @media (prefers-reduced-motion: reduce) {
      .entra, .digitando, .digitando span { animation: none; opacity: 1; }
      .digitando { display: none; }
    }
    .celular-topo {
      display: flex; align-items: center; gap: 8px;
      font-size: 0.82rem; color: var(--texto-suave); font-weight: 600;
      padding-bottom: 12px; border-bottom: 1px solid rgba(201, 169, 255, 0.16); margin-bottom: 14px;
    }
    .bolinha { width: 9px; height: 9px; border-radius: 50%; background: var(--verde-500); }
    .balao { font-size: 0.85rem; line-height: 1.5; padding: 11px 14px; border-radius: 14px; margin-bottom: 10px; }
    .balao.recebido { background: var(--superficie); border: 1px solid var(--borda); border-bottom-left-radius: 4px; }
    .balao.enviado {
      background: var(--verde-500); color: #fff; margin-left: auto; width: fit-content;
      border-bottom-right-radius: 4px; font-weight: 600; padding: 8px 18px;
    }
    .opcoes {
      margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--borda);
      color: var(--texto-suave); font-size: 0.8rem;
    }
    .etiqueta-status {
      display: flex; align-items: center; gap: 6px; justify-content: center;
      font-size: 0.75rem; color: var(--alerta); background: var(--alerta-bg);
      padding: 7px; border-radius: 8px; margin-top: 6px;
    }
    .etiqueta-status mat-icon { font-size: 15px; width: 15px; height: 15px; }

    /* faixas */
    .faixa { padding: 72px 28px; max-width: 1060px; margin: 0 auto; text-align: center; }
    /* A faixa clara não pode ser só cinza claro entre duas faixas escuras,
       senão vira o vão entre elas. Ganha luz própria, da mesma família. */
    /* Sem luz aqui, de propósito. Quando toda seção tem a sua aurora, a luz
       deixa de ser acontecimento e vira textura de fundo: o olho para de
       registrar. A página passa a alternar seção acesa e seção calma, e é a
       alternância que cria o ritmo. Esta é calma. */
    .faixa.claro {
      position: relative;
      background-color: var(--fundo-700); max-width: none;
      border-top: 1px solid rgba(201, 169, 255, 0.08);
      border-bottom: 1px solid rgba(201, 169, 255, 0.08);
    }
    .faixa.claro > * { max-width: 1060px; margin-left: auto; margin-right: auto; }
    .faixa h2 {
      font-size: clamp(1.9rem, 3.4vw, 2.9rem);
      margin: 0 0 12px; letter-spacing: -0.03em; line-height: 1.04;
    }
    .secao-texto { color: var(--texto-suave); margin: 0 auto 40px; max-width: 40em; font-size: 1.02rem; }

    /* dados da pesquisa */
    /* A faixa da pesquisa é o pico da página: fundo petróleo, muito mais
       profundo que o verde, com o lima acendendo de baixo. É o contraste que
       faltava. Verde sobre verde não brilha. */
    /* A faixa da pesquisa é o pico da página, e agora tem uma fotografia por
       baixo. Ela entra como textura, não como ilustração: fica escura,
       tingida de ameixa e coberta pelo roxo, de modo que o olho registre
       profundidade e presença humana sem parar para olhar a foto.

       Foto de pessoa diante de um laptop num escritório bem iluminado é uma
       das imagens mais repetidas da internet. Tratada assim, deixa de se ler
       como retrato de catálogo e passa a ser atmosfera. */
    .problema {
      position: relative; overflow: hidden; max-width: none;
      background-color: var(--fundo-900);
    }
    .problema::before {
      content: ""; position: absolute; inset: 0;
      background-image: url("/assets/equipe-trabalhando.webp");
      background-size: cover;
      background-position: 70% 40%;
      /* Dessaturada e escurecida antes mesmo da camada de cor: assim o roxo
         por cima tinge uma imagem neutra, e não briga com o azul da janela
         e o verde da planta que havia na foto original. */
      filter: grayscale(1) brightness(0.42) contrast(1.1);
      opacity: 0.5;
    }
    /* A camada de cor por cima da foto. Separada do ::before para que a foto
       possa ser filtrada sem o filtro alcançar o roxo. */
    .problema::after {
      content: ""; position: absolute; inset: 0; pointer-events: none;
      background-image:
        radial-gradient(40rem 26rem at 82% -6%, rgba(134, 99, 187, 0.62), transparent 62%),
        radial-gradient(34rem 26rem at 10% 112%, rgba(201, 169, 255, 0.38), transparent 60%),
        linear-gradient(160deg, rgba(15, 11, 20, 0.86) 0%, rgba(30, 23, 38, 0.80) 100%);
    }
    /* O conteúdo precisa subir acima das duas camadas. */
    .problema > * { position: relative; z-index: 1; }
    .problema h2, .problema .secao-texto { color: #fff; }
    .problema .secao-texto { opacity: 0.85; }
    /* Três números enormes lado a lado é o painel de métricas que toda página
       de produto exibe, e some do olho justamente por isso. Aqui são achados
       de pesquisa, então se leem como achados: um por linha, o número à
       esquerda na largura de uma coluna, a frase ao lado, filete entre eles.
       O número perdeu o brilho em volta: luz colorida atrás de texto é
       enfeite, e aqui ela competia com a própria leitura. */
    .numeros {
      max-width: 760px; margin: 0 auto; text-align: left;
    }
    /* As três linhas entram escalonadas quando a seção chega na tela.
       Lista que aparece como lista justifica o escalonamento; o resto da
       página não ganha isso de propósito, porque animar toda seção ao rolar
       é o efeito mais cansativo que existe e cancela a si mesmo.

       O atraso total é curto (0,24s entre a primeira e a última): escalonar
       demais faz esperar, e esperar por enfeite irrita. */
    /* O esconde depende da classe "pronta", que só o próprio componente põe
       depois de montar. Sem ela, os números aparecem normalmente.
       Importa: se o script falhar, ou o navegador não tiver
       IntersectionObserver, a classe "visivel" nunca chega, e sem esta
       precaução os três números ficariam invisíveis para sempre. Conteúdo
       que depende de animação para existir é conteúdo que some sozinho. */
    .numeros.pronta:not(.visivel) .numero { opacity: 0; }
    .numeros.visivel .numero {
      animation: sobe 560ms cubic-bezier(0.16, 1, 0.3, 1) backwards;
    }
    .numeros.visivel .numero:nth-child(2) { animation-delay: 0.12s; }
    .numeros.visivel .numero:nth-child(3) { animation-delay: 0.24s; }

    @keyframes sobe {
      from { opacity: 0; transform: translateY(14px); }
      to   { opacity: 1; transform: none; }
    }

    /* Com menos movimento pedido, as três aparecem juntas e paradas. */
    @media (prefers-reduced-motion: reduce) {
      .numeros.pronta:not(.visivel) .numero { opacity: 1; }
      .numeros.visivel .numero { animation: none; }
    }

    .numero {
      display: grid; grid-template-columns: 5.4rem 1fr;
      gap: 0 28px; align-items: baseline;
      padding: 22px 0;
      border-top: 1px solid rgba(201, 169, 255, 0.18);
    }
    .numero:last-child { border-bottom: 1px solid rgba(201, 169, 255, 0.18); }
    .numero dt {
      font-family: "Outfit", "Hanken Grotesk", sans-serif;
      font-size: 2.3rem; font-weight: 600;
      color: var(--lilas-300);
      line-height: 1; letter-spacing: -0.04em;
      font-variant-numeric: tabular-nums;
    }
    .numero dd {
      margin: 0; font-size: 1rem; line-height: 1.5;
      color: #fff; opacity: 0.88;
    }

    /* passos
       Quatro cartões iguais lado a lado não dizem que existe uma ordem: dizem
       que existem quatro coisas. Aqui os passos ficam enfileirados sobre um
       trilho, com os números apoiados nele. A linha é que conta a sequência,
       e as caixas somem. */
    .passos {
      position: relative;
      display: grid; grid-template-columns: repeat(4, 1fr);
      gap: 22px; text-align: left;
      padding-top: 6px;
    }
    /* O trilho passa pelo centro dos números e para no primeiro e no último,
       em vez de sangrar para fora da sequência. */
    .passos::before {
      content: "";
      position: absolute;
      top: 23px; left: calc(12.5% + 17px); right: calc(12.5% + 17px);
      height: 2px;
      background-image: linear-gradient(90deg,
        rgba(201, 169, 255, 0.10) 0%, rgba(201, 169, 255, 0.45) 50%,
        rgba(201, 169, 255, 0.10) 100%);
    }
    .passo { position: relative; padding: 0 4px 0 0; }
    .passo-numero {
      display: flex; align-items: center; justify-content: center;
      width: 34px; height: 34px; border-radius: 50%;
      /* Chapado, não em degradê: a pastilha colorida com brilho é o enfeite
         que acompanha toda sequência 1-2-3 por aí. O número precisa marcar
         posição no trilho, não brilhar. */
      background: var(--ameixa-700);
      border: 1px solid rgba(201, 169, 255, 0.34);
      color: var(--lilas-300); font-weight: 600; margin-bottom: 16px;
      font-variant-numeric: tabular-nums;
      /* O anel na cor do fundo abre um vão no trilho em volta do número. */
      box-shadow:
        0 0 0 6px var(--fundo),
        inset 0 1px 0 rgba(255, 255, 255, 0.25),
        0 2px 6px -1px rgba(39, 26, 56, 0.4);
    }
    .passo h3 { font-size: 1rem; margin: 0 0 6px; }
    .passo p { font-size: 0.88rem; color: var(--texto-suave); margin: 0; line-height: 1.55;
               max-width: 22em; }

    /* Recursos como índice, não como cartões.
       Seis caixas iguais, cada uma com um ícone em cima, um título e um
       parágrafo, é o arranjo mais repetido da internet e a assinatura mais
       reconhecível de página gerada por máquina. Sai a moldura, sai o ícone
       decorativo, e fica o que interessa: a lista do que a pessoa deixa de
       fazer. O filete em cima de cada item separa sem desenhar uma caixa. */
    .recursos {
      display: grid; grid-template-columns: repeat(2, 1fr);
      gap: 0 52px; text-align: left; padding-bottom: 34px;
      list-style: none; margin: 0;
    }
    .recurso {
      padding: 26px 0 28px;
      border-top: 1px solid rgba(201, 169, 255, 0.14);
    }
    /* O título assume o peso que a moldura carregava. Numa lista sem caixa,
       quem separa um item do outro é a diferença de tamanho e de cor entre o
       título e o texto, não uma borda em volta. */
    .recurso h3 {
      font-size: 1.16rem; margin: 0 0 8px;
      letter-spacing: -0.018em; color: var(--texto);
    }
    .recurso p {
      font-size: 0.93rem; color: var(--texto-suave); margin: 0;
      line-height: 1.62; max-width: 34em;
    }

    /* garantias */
    .garantias { display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px; text-align: left; }
    .garantia { display: flex; gap: 14px; }
    .garantia mat-icon { color: var(--lilas-300); flex: none; }
    .garantia h3 { font-size: 1rem; margin: 0 0 6px; }
    .garantia p { font-size: 0.88rem; color: var(--texto-suave); margin: 0; line-height: 1.55; }

    /* Chamada final: luzes radiais sobre o verde escuro, em vez do degradê
       linear de 45°, que é a assinatura mais reconhecível de tela gerada por IA. */
    /* O fecho é o ponto mais escuro da página. Sem brilho atrás: quem tem de
       acender aqui é o botão, e luz em volta dele tira dele a atenção. */
    .chamada {
      position: relative;
      background-color: var(--fundo-900);
      border-top: 1px solid rgba(201, 169, 255, 0.10);
      padding: 92px 28px; text-align: center;
    }
    .chamada h2 { color: #fff; font-size: 1.9rem; margin: 0 0 10px; }
    .chamada p { color: #fff; opacity: 0.85; margin: 0 0 28px; }
    .botao-claro { background: var(--lilas-300) !important; color: var(--fundo-900) !important; }

    /* rodapé */
    .rodape {
      display: flex; flex-direction: column; align-items: center; gap: 6px;
      padding: 34px 28px; background: var(--superficie); border-top: 1px solid var(--borda);
      font-size: 0.85rem; color: var(--texto-suave); text-align: center;
    }
    /* Exigência da LGPD, e também o item que mais falta em página gerada:
       documento publicado que ninguém acha é o mesmo que inexistente. */
    .rodape-links { display: flex; gap: var(--vao-grupo); flex-wrap: wrap; }
    .rodape-links a {
      color: var(--texto-suave); text-decoration: none; font-size: 0.88rem;
    }
    .rodape-links a:hover { color: var(--lilas-300); text-decoration: underline; }
    .rodape-fraco { color: var(--texto-fraco); font-size: 0.8rem; }

    /* telas menores */
    @media (max-width: 900px) {
      .capa { grid-template-columns: 1fr; gap: 40px; padding: 44px 20px 60px; text-align: center; }
      .capa h1 { font-size: 2rem; }
      .subtitulo { margin-left: auto; margin-right: auto; }
      .recursos { grid-template-columns: repeat(2, 1fr); }
      .garantias { grid-template-columns: repeat(2, 1fr); }
      /* Em duas colunas o trilho horizontal deixaria de acompanhar a ordem
         (que passa a ser em zigue-zague): sai de cena. */
      .passos { grid-template-columns: repeat(2, 1fr); row-gap: 30px; }
      .passos::before { display: none; }
      .faixa { padding: 52px 20px; }
    }
    @media (max-width: 600px) {
      /* Uma coluna: o desencontro deixa de fazer sentido e vira buraco. */
      .recursos > :nth-child(even) { margin-top: 0; }
      .recursos { padding-bottom: 0; }
      .topo { padding: 10px 16px; }
      .capa h1 { font-size: 1.75rem; }
      .numeros, .recursos, .garantias, .passos { grid-template-columns: 1fr; }
      .numero strong { font-size: 2.2rem; }
      .celular { width: 100%; max-width: 300px; }
      .btn-grande { width: 100%; }
    }
  `],
})
export class LoginComponent implements AfterViewInit, OnDestroy {
  private observador?: IntersectionObserver;

  /**
   * Liga o escalonamento das linhas da pesquisa quando elas chegam na tela.
   *
   * Observador em vez de animar no carregamento: a faixa fica abaixo da
   * dobra, e animar no load faria o movimento acontecer sem ninguém ver.
   *
   * Observa uma vez e desliga. Deixar o observador vivo depois de a animação
   * ter rodado é trabalho a cada rolagem, para nada.
   *
   * Se o navegador não tiver IntersectionObserver, ou se o script falhar, a
   * classe nunca é posta e as linhas ficam visíveis paradas: o conteúdo
   * nunca depende da animação para existir.
   */
  ngAfterViewInit(): void {
    const numeros = document.querySelector('.numeros');
    if (!numeros || !('IntersectionObserver' in window)) return;

    // Só agora os números podem começar escondidos: a partir daqui existe
    // script vivo para revelá-los.
    numeros.classList.add('pronta');

    this.observador = new IntersectionObserver(
      (entradas) => {
        for (const entrada of entradas) {
          if (!entrada.isIntersecting) continue;
          entrada.target.classList.add('visivel');
          this.observador?.unobserve(entrada.target);
        }
      },
      // Dispara quando um quarto da faixa apareceu: esperar a seção inteira
      // faria a animação rodar depois de a pessoa já estar lendo.
      { threshold: 0.25 },
    );
    this.observador.observe(numeros);
  }

  ngOnDestroy(): void {
    this.observador?.disconnect();
  }

  private auth = inject(AuthService);
  readonly recursos = RECURSOS;
  readonly passos = PASSOS;
  /** Atualiza sozinho na virada do ano. */
  readonly ano = new Date().getFullYear();

  entrar(): void {
    this.auth.entrarComGoogle();
  }
}
