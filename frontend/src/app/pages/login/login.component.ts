import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/auth.service';

interface Recurso { icone: string; titulo: string; texto: string; }
interface Passo { numero: string; titulo: string; texto: string; }

const RECURSOS: Recurso[] = [
  {
    icone: 'people',
    titulo: 'Carteira de clientes',
    texto: 'Cadastro completo com histórico de compras, pagamentos e o saldo devedor de cada pessoa sempre à mão.',
  },
  {
    icone: 'send',
    titulo: 'Cobrança automática',
    texto: 'O sistema envia a mensagem no WhatsApp na data certa: lembrete antes, aviso no vencimento e cobrança no atraso.',
  },
  {
    icone: 'chat',
    titulo: 'Mensagens do seu jeito',
    texto: 'Modelos personalizáveis que preenchem sozinhos o nome, o valor e a data. Você escreve uma vez e o sistema usa sempre.',
  },
  {
    icone: 'insights',
    titulo: 'Painel financeiro',
    texto: 'Quanto você tem a receber, quanto já recebeu no mês e quanto está em atraso, tudo em uma tela só.',
  },
  {
    icone: 'leaderboard',
    titulo: 'Ranking de pagadores',
    texto: 'O sistema classifica quem paga em dia e quem costuma atrasar, com base no histórico real de cada cliente.',
  },
  {
    icone: 'summarize',
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
  imports: [MatButtonModule, MatIconModule],
  template: `
    <div class="pagina">

      <header class="topo">
        <span class="marca"><mat-icon>task_alt</mat-icon> TáEmDia</span>
        <button mat-flat-button color="primary" (click)="entrar()">Entrar</button>
      </header>

      <section class="capa">
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

        <div class="capa-visual" aria-hidden="true">
          <div class="celular">
            <div class="celular-topo"><span class="bolinha"></span> Cliente</div>
            <div class="balao recebido">
              Olá Rosangela! Passando para lembrar que sua parcela de
              <strong>R$ 100,00</strong> vence em <strong>10/09</strong>.
              <div class="opcoes">1 - Já paguei<br>2 - Vou pagar hoje<br>3 - Não consigo pagar</div>
            </div>
            <div class="balao enviado">1</div>
            <div class="etiqueta-status"><mat-icon>schedule</mat-icon> Aguardando sua confirmação</div>
          </div>
        </div>
      </section>

      <section class="faixa problema com-grao">
        <h2>Cobrar manualmente custa caro</h2>
        <p class="secao-texto">
          Em pesquisa com pequenos empreendedores que vendem parcelado, o retrato foi este:
        </p>
        <div class="numeros">
          <div class="numero">
            <strong>100%</strong>
            <span>vendem parcelado e precisam controlar vencimentos</span>
          </div>
          <div class="numero">
            <strong>83%</strong>
            <span>cobram manualmente, uma mensagem de cada vez</span>
          </div>
          <div class="numero">
            <strong>50%</strong>
            <span>têm dificuldade de cobrar sem parecer insistente</span>
          </div>
        </div>
      </section>

      <section class="faixa">
        <h2>Como funciona</h2>
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
        <h2>O que o sistema faz</h2>
        <p class="secao-texto">Tudo o que você precisa para não perder um vencimento.</p>
        <div class="recursos">
          @for (r of recursos; track r.titulo) {
            <div class="recurso">
              <span class="recurso-icone"><mat-icon>{{ r.icone }}</mat-icon></span>
              <h3>{{ r.titulo }}</h3>
              <p>{{ r.texto }}</p>
            </div>
          }
        </div>
      </section>

      <section class="faixa">
        <h2>Feito com cuidado</h2>
        <div class="garantias">
          <div class="garantia">
            <mat-icon>verified_user</mat-icon>
            <div>
              <h3>Você decide o que é pago</h3>
              <p>Se o cliente responder "já paguei", a parcela fica aguardando sua conferência. Só você dá baixa.</p>
            </div>
          </div>
          <div class="garantia">
            <mat-icon>schedule</mat-icon>
            <div>
              <h3>Sem incomodar fora de hora</h3>
              <p>As mensagens saem apenas em horário comercial, com limite diário por cliente.</p>
            </div>
          </div>
          <div class="garantia">
            <mat-icon>lock</mat-icon>
            <div>
              <h3>Seus dados são só seus</h3>
              <p>Entrada pela conta Google, sem senha guardada, e cada conta enxerga apenas os próprios clientes.</p>
            </div>
          </div>
        </div>
      </section>

      <section class="chamada com-grao">
        <h2>Comece agora</h2>
        <p>Leva menos de um minuto para cadastrar o primeiro cliente.</p>
        <button mat-flat-button class="btn-grande botao-claro" (click)="entrar()">
          <mat-icon>login</mat-icon> Continuar com Google
        </button>
      </section>

      <footer class="rodape">
        <span><strong>TáEmDia</strong> — Cobrança automatizada via WhatsApp</span>
        <span class="rodape-fraco">© {{ ano }} TáEmDia</span>
      </footer>
    </div>
  `,
  styles: [`
    .pagina { background: var(--superficie); }
    h1, h2, h3 { color: var(--texto); }

    /* topo fixo */
    .topo {
      position: sticky; top: 0; z-index: 10;
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 28px;
      background: rgba(255, 255, 255, 0.92);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--borda);
    }
    .marca {
      display: flex; align-items: center; gap: 8px;
      font-weight: 600; font-size: 1.15rem; color: var(--verde-800);
    }

    /* apresentação */
    .capa {
      display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 48px; align-items: center;
      padding: 72px 28px 88px; max-width: 1100px; margin: 0 auto;
    }
    .selo {
      display: inline-block; background: var(--verde-50); color: var(--verde-800);
      padding: 6px 14px; border-radius: 999px; font-size: 0.8rem; font-weight: 600;
      margin-bottom: 18px;
    }
    .capa h1 { font-size: 2.7rem; line-height: 1.15; margin: 0 0 18px; letter-spacing: -0.5px; }

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
    .destaque { color: var(--verde-700); }
    .subtitulo { font-size: 1.1rem; color: var(--texto-suave); line-height: 1.6; margin: 0 0 28px; max-width: 30em; }
    .btn-grande { height: 50px; padding: 0 28px !important; font-size: 1rem; }
    .btn-grande mat-icon { margin-right: 8px; }
    .aviso { font-size: 0.82rem; color: var(--texto-fraco); margin-top: 14px; }

    /* ilustração da conversa */
    .capa-visual { display: flex; justify-content: center; }
    .celular {
      position: relative;
      width: 300px; background: var(--verde-50); border: 1px solid var(--verde-100);
      border-radius: 22px; padding: 16px;
      /* Sombra em camadas: contato curto e escuro perto do objeto, difusa e
         clara longe. Uma sombra só, grande e uniforme, boia. */
      box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.8),
        0 1px 2px rgba(15, 98, 52, 0.10),
        0 8px 16px -6px rgba(15, 98, 52, 0.14),
        0 28px 56px -20px rgba(15, 98, 52, 0.28);
    }
    /* Reflexo no vidro: uma faixa clara na diagonal do canto superior. */
    .celular::after {
      content: ""; position: absolute; inset: 0; border-radius: 22px;
      pointer-events: none;
      background: linear-gradient(152deg, rgba(255, 255, 255, 0.55) 0%,
                                  rgba(255, 255, 255, 0) 38%);
    }
    .celular > * { position: relative; z-index: 1; }
    .celular-topo {
      display: flex; align-items: center; gap: 8px;
      font-size: 0.82rem; color: var(--texto-suave); font-weight: 600;
      padding-bottom: 12px; border-bottom: 1px solid var(--verde-100); margin-bottom: 14px;
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
    .faixa.claro { background: var(--fundo); max-width: none; }
    .faixa.claro > * { max-width: 1060px; margin-left: auto; margin-right: auto; }
    .faixa h2 { font-size: 1.9rem; margin: 0 0 10px; letter-spacing: -0.3px; }
    .secao-texto { color: var(--texto-suave); margin: 0 auto 40px; max-width: 40em; font-size: 1.02rem; }

    /* dados da pesquisa */
    .problema {
      position: relative; overflow: hidden; max-width: none;
      background-color: var(--verde-900);
      background-image:
        radial-gradient(44rem 30rem at 78% 8%, rgba(41, 148, 91, 0.40), transparent 62%),
        radial-gradient(30rem 22rem at 6% 100%, rgba(60, 182, 118, 0.22), transparent 58%);
    }
    .problema h2, .problema .secao-texto { color: #fff; }
    .problema .secao-texto { opacity: 0.85; }
    .numeros { display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; max-width: 900px; margin: 0 auto; }
    .numero { color: #fff; }
    .numero strong { display: block; font-size: 2.8rem; color: var(--verde-100); line-height: 1; margin-bottom: 10px; }
    .numero span { font-size: 0.92rem; opacity: 0.85; line-height: 1.5; display: block; }

    /* passos
       Quatro cartões iguais lado a lado não dizem que existe uma ordem: dizem
       que existem quatro coisas. Aqui os passos ficam enfileirados sobre um
       trilho, com os números apoiados nele — a linha é que conta a sequência,
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
        var(--verde-100) 0%, var(--verde-300) 50%, var(--verde-100) 100%);
    }
    .passo { position: relative; padding: 0 4px 0 0; }
    .passo-numero {
      display: flex; align-items: center; justify-content: center;
      width: 34px; height: 34px; border-radius: 50%;
      background-image: linear-gradient(180deg, var(--verde-700) 0%, var(--verde-900) 100%);
      color: #fff; font-weight: 700; margin-bottom: 16px;
      /* O anel na cor do fundo abre um vão no trilho em volta do número. */
      box-shadow:
        0 0 0 6px var(--fundo),
        inset 0 1px 0 rgba(255, 255, 255, 0.25),
        0 2px 6px -1px rgba(15, 98, 52, 0.4);
    }
    .passo h3 { font-size: 1rem; margin: 0 0 6px; }
    .passo p { font-size: 0.88rem; color: var(--texto-suave); margin: 0; line-height: 1.55;
               max-width: 22em; }

    /* Recursos em duas colunas desencontradas.
       Três colunas iguais é o arranjo mais previsível que existe; o desencontro
       cria ritmo e faz o olho percorrer em ziguezague. */
    .recursos {
      display: grid; grid-template-columns: repeat(2, 1fr);
      gap: 22px 24px; text-align: left; padding-bottom: 34px;
    }
    /* Desencontro com margem (não transform): funciona em qualquer motor de
       renderização e não depende de composição de camadas. */
    .recursos > :nth-child(even) { margin-top: 34px; }
    .recurso {
      background: var(--superficie); border: 1px solid var(--borda);
      border-radius: var(--raio); padding: 28px 26px;
      transition: transform 250ms ease, box-shadow 250ms ease;
    }
    .recurso-icone {
      display: flex; align-items: center; justify-content: center;
      width: 46px; height: 46px; border-radius: 12px;
      background: var(--verde-50); color: var(--verde-800); margin-bottom: 16px;
    }
    .recurso h3 { font-size: 1.05rem; margin: 0 0 8px; }
    .recurso p { font-size: 0.9rem; color: var(--texto-suave); margin: 0; line-height: 1.6; }

    /* garantias */
    .garantias { display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px; text-align: left; }
    .garantia { display: flex; gap: 14px; }
    .garantia mat-icon { color: var(--verde-700); flex: none; }
    .garantia h3 { font-size: 1rem; margin: 0 0 6px; }
    .garantia p { font-size: 0.88rem; color: var(--texto-suave); margin: 0; line-height: 1.55; }

    /* Chamada final: luzes radiais sobre o verde escuro, em vez do degradê
       linear de 45° — que é a assinatura mais reconhecível de tela gerada por IA. */
    .chamada {
      position: relative; overflow: hidden;
      background-color: var(--verde-900);
      background-image:
        radial-gradient(38rem 26rem at 22% 0%, rgba(60, 182, 118, 0.42), transparent 62%),
        radial-gradient(32rem 24rem at 88% 110%, rgba(41, 148, 91, 0.38), transparent 60%);
      padding: 76px 28px; text-align: center;
    }
    .chamada h2 { color: #fff; font-size: 1.9rem; margin: 0 0 10px; }
    .chamada p { color: #fff; opacity: 0.85; margin: 0 0 28px; }
    .botao-claro { background: #fff !important; color: var(--verde-900) !important; }

    /* rodapé */
    .rodape {
      display: flex; flex-direction: column; align-items: center; gap: 6px;
      padding: 34px 28px; background: var(--superficie); border-top: 1px solid var(--borda);
      font-size: 0.85rem; color: var(--texto-suave); text-align: center;
    }
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
export class LoginComponent {
  private auth = inject(AuthService);
  readonly recursos = RECURSOS;
  readonly passos = PASSOS;
  /** Atualiza sozinho na virada do ano. */
  readonly ano = new Date().getFullYear();

  entrar(): void {
    this.auth.entrarComGoogle();
  }
}
