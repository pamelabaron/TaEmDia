import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { AuthService } from './core/auth.service';
import { AssinaturaService } from './core/assinatura.service';

interface ItemMenu { rota: string; titulo: string; icone: string; }

/**
 * Cada ícone é escolhido pelo que a palavra significa, não pelo que sobra:
 * o painel mostra quadros de números, clientes são pessoas, ranking é um
 * pódio, cobrança é mensagem que sai, mensagens são conversas.
 */
const MENU: ItemMenu[] = [
  { rota: '/painel', titulo: 'Painel', icone: 'space_dashboard' },
  { rota: '/clientes', titulo: 'Clientes', icone: 'groups' },
  { rota: '/ranking', titulo: 'Ranking', icone: 'emoji_events' },
  { rota: '/cobrancas', titulo: 'Cobranças', icone: 'outgoing_mail' },
  { rota: '/mensagens', titulo: 'Mensagens', icone: 'forum' },
  { rota: '/whatsapp', titulo: 'WhatsApp', icone: 'chat' },
  { rota: '/cobranca-automatica', titulo: 'Cobrança automática', icone: 'schedule_send' },
  { rota: '/resumo-diario', titulo: 'Resumo diário', icone: 'summarize' },
];

/** Lembra se a barra está encolhida, para não reabrir a cada visita. */
const CHAVE_ENCOLHIDA = 'taemdia_barra_encolhida';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet, RouterLink, RouterLinkActive,
    MatToolbarModule, MatButtonModule, MatIconModule, MatMenuModule, MatTooltipModule,
  ],
  template: `
    @if (auth.logado()) {
      <div class="estrutura" [class.encolhida]="encolhida()">

        <!-- ============================================ navegação lateral
             No computador a navegação fica na lateral: cabe ícone e rótulo
             lado a lado, e o menu não compete com o título da página.
             No celular ela vira a barra de cima com menu sanduíche: uma
             coluna fixa comeria metade de uma tela de 375px. -->
        <aside class="lateral">
          <div class="topo-lateral">
            <a class="marca" routerLink="/painel">
              <mat-icon>task_alt</mat-icon>
              <span class="rotulo">TáEmDia</span>
            </a>
            <button class="encolher" (click)="alternarBarra()"
                    [matTooltip]="encolhida() ? 'Expandir menu' : 'Encolher menu'"
                    matTooltipPosition="right"
                    [attr.aria-label]="encolhida() ? 'Expandir menu' : 'Encolher menu'">
              <mat-icon>{{ encolhida() ? 'chevron_right' : 'chevron_left' }}</mat-icon>
            </button>
          </div>

          <nav>
            @for (item of menu; track item.rota) {
              <a [routerLink]="item.rota" routerLinkActive="ativo" class="item"
                 [matTooltip]="encolhida() ? item.titulo : ''" matTooltipPosition="right">
                <mat-icon>{{ item.icone }}</mat-icon>
                <span class="rotulo">{{ item.titulo }}</span>
              </a>
            }
            @if (auth.administrador()) {
              <a routerLink="/assinaturas" routerLinkActive="ativo" class="item"
                 [matTooltip]="encolhida() ? 'Comprovantes' : ''" matTooltipPosition="right">
                <mat-icon>receipt_long</mat-icon>
                <span class="rotulo">Comprovantes</span>
              </a>
            }
          </nav>

          <!-- Bloco da pessoa. Fica no rodapé porque é sobre quem usa, não
               sobre para onde ir. O Sair mora dentro do menu: é saída, e
               saída não deve ficar a um clique de distância por engano. -->
          <button class="pessoa" [matMenuTriggerFor]="menuPessoa"
                  [matTooltip]="encolhida() ? (auth.vendedor()?.nome ?? '') : ''"
                  matTooltipPosition="right">
            <span class="avatar">
              <!-- A foto vem de um servidor do Google, que pode recusar ou
                   remover o arquivo. Quando isso acontece, cai nas iniciais em
                   vez de deixar um quadro quebrado. O alt fica vazio de
                   propósito: o nome está escrito ao lado, e repeti-lo faria o
                   leitor de tela dizer a mesma coisa duas vezes. -->
              @if (auth.vendedor()?.foto_url && !fotoFalhou()) {
                <img [src]="auth.vendedor()!.foto_url" alt="" referrerpolicy="no-referrer"
                     (error)="fotoFalhou.set(true)" />
              } @else {
                <span class="iniciais">{{ auth.iniciais() || '?' }}</span>
              }
            </span>
            <span class="quem rotulo">
              <span class="nome">{{ auth.vendedor()?.nome ?? 'Carregando' }}</span>
            </span>
            <mat-icon class="seta rotulo">expand_less</mat-icon>
          </button>

          <mat-menu #menuPessoa="matMenu" class="menu-pessoa" xPosition="after">
            <div class="cabecalho-menu" (click)="$event.stopPropagation()">
              <span class="nome">{{ auth.vendedor()?.nome }}</span>
              <span class="email">{{ auth.vendedor()?.google_email }}</span>
            </div>

            <a mat-menu-item routerLink="/minha-assinatura">
              <mat-icon>card_membership</mat-icon>
              <span>Minha assinatura</span>
            </a>
            @if (auth.administrador()) {
              <a mat-menu-item routerLink="/assinaturas">
                <mat-icon>receipt_long</mat-icon>
                <span>Comprovantes</span>
              </a>
            }

            <div class="divisor"></div>
            <button mat-menu-item class="sair" (click)="auth.sair()">
              <mat-icon>logout</mat-icon>
              <span>Sair</span>
            </button>
          </mat-menu>
        </aside>

        <!-- ================================================ barra do celular -->
        <mat-toolbar color="primary" class="barra-mobile">
          <button mat-icon-button [matMenuTriggerFor]="menuMobile" aria-label="Abrir menu">
            <mat-icon>menu</mat-icon>
          </button>
          <mat-menu #menuMobile="matMenu">
            <div class="cabecalho-menu" (click)="$event.stopPropagation()">
              <span class="nome">{{ auth.vendedor()?.nome }}</span>
              <span class="email">{{ auth.vendedor()?.google_email }}</span>
            </div>
            @for (item of menu; track item.rota) {
              <a mat-menu-item [routerLink]="item.rota">
                <mat-icon>{{ item.icone }}</mat-icon>
                <span>{{ item.titulo }}</span>
              </a>
            }
            @if (auth.administrador()) {
              <a mat-menu-item routerLink="/assinaturas">
                <mat-icon>receipt_long</mat-icon>
                <span>Comprovantes</span>
              </a>
            }
            <div class="divisor"></div>
            <button mat-menu-item class="sair" (click)="auth.sair()">
              <mat-icon>logout</mat-icon>
              <span>Sair</span>
            </button>
          </mat-menu>

          <span class="marca-mobile"><mat-icon>task_alt</mat-icon> TáEmDia</span>
        </mat-toolbar>

        <!-- ==================================================== conteúdo -->
        <main class="conteudo">
          <!-- Aviso de vigência. Aparece só quando há o que avisar: sistema
               que avisa o tempo todo deixa de ser lido. -->
          @if (assinatura.bloqueada()) {
            <a class="faixa vencida" routerLink="/minha-assinatura">
              <mat-icon inline>lock</mat-icon>
              Sua assinatura venceu. Você continua vendo tudo, mas não consegue cadastrar nem
              cobrar. <strong>Renovar</strong>
            </a>
          } @else {
            @if (assinatura.acabando(); as dias) {
              <a class="faixa acabando" routerLink="/minha-assinatura">
                <mat-icon inline>schedule</mat-icon>
                Seu período de teste termina em {{ dias }} {{ dias === 1 ? 'dia' : 'dias' }}.
                <strong>Assinar</strong>
              </a>
            }
          }
          <router-outlet></router-outlet>
        </main>
      </div>
    } @else {
      <router-outlet></router-outlet>
    }
  `,
  styles: [`
    /* ------------------------------------------------------------ estrutura */
    .estrutura { display: grid; grid-template-columns: 250px 1fr; min-height: 100dvh; }
    /* A largura é o único valor que muda ao encolher: tudo o mais reage a ela. */
    .estrutura.encolhida { grid-template-columns: 74px 1fr; }
    .conteudo {
      /* Coluna 2 dita na mão: com a barra fora do fluxo (posição fixa), o
         conteúdo seria colocado na coluna 1 e ficaria por baixo dela. */
      grid-column: 2;
      min-width: 0; /* sem isto, conteúdo largo empurra a lateral */
      /* Sem a barra de cima, o título encostava na borda. O respiro maior em
         cima do que embaixo é o que faz o cabeçalho pertencer ao conteúdo que
         vem depois dele, e não flutuar. */
      padding-top: 14px;
    }
    @media (max-width: 959px) { .conteudo { padding-top: 0; } }

    /* -------------------------------------------------------- barra lateral */
    /* A coluna não rola com a página e nunca passa da altura da tela: quem
       rola, quando precisa, é só a lista de itens por dentro. Antes o bloco da
       pessoa escorregava para fora do fundo e aparecia branco. */
    .lateral {
      /* Presa à janela, não ao documento: assim não se mexe com a rolagem e
         não depende de 100dvh, que em alguns navegadores devolve um valor
         diferente da altura visível e empurrava o bloco da pessoa para fora
         da tela. A coluna da grade continua reservando a largura. */
      position: fixed; top: 0; left: 0; bottom: 0;
      /* border-box para a largura incluir o espaçamento interno: sem isso a
         coluna media 274px e cobria um pedaço do conteúdo. */
      box-sizing: border-box; width: 250px; overflow: hidden;
      display: flex; flex-direction: column;
      padding: 16px 12px 14px;
      background-color: var(--petroleo-900);
      background-image:
        radial-gradient(20rem 16rem at 8% 100%, rgba(201, 169, 255, 0.30), transparent 66%),
        radial-gradient(22rem 18rem at 100% 0%, rgba(134, 99, 187, 0.34), transparent 62%),
        linear-gradient(168deg, var(--petroleo-800) 0%, var(--petroleo-900) 100%);
      box-shadow: inset -1px 0 0 rgba(201, 169, 255, 0.14);
      /* Sem transição aqui de propósito: animar padding obriga o navegador a
         refazer o layout a cada quadro, e a largura da coluna já muda de uma
         vez (a grade não é animada). Meia animação fica pior que nenhuma. */
    }
    .encolhida .lateral { width: 74px; padding-left: 10px; padding-right: 10px; }

    .topo-lateral {
      display: flex; align-items: center; justify-content: space-between;
      gap: 6px; margin-bottom: 16px; flex-shrink: 0;
    }
    .marca {
      display: flex; align-items: center; gap: 10px;
      padding: 6px 4px 0 8px;
      color: #fff; text-decoration: none;
      font-family: "Outfit", sans-serif;
      font-weight: 600; font-size: 1.1rem; letter-spacing: -0.02em;
      min-width: 0;
    }
    .marca mat-icon { color: var(--lima-400); flex-shrink: 0; }

    .encolher {
      display: flex; align-items: center; justify-content: center;
      width: 30px; height: 30px; flex-shrink: 0;
      border: 1px solid rgba(255, 255, 255, 0.14); border-radius: 8px;
      background: rgba(255, 255, 255, 0.05); color: rgba(255, 255, 255, 0.8);
      cursor: pointer; padding: 0;
      transition: background-color 160ms ease, color 160ms ease;
    }
    .encolher mat-icon { font-size: 19px; width: 19px; height: 19px; }
    @media (hover: hover) and (pointer: fine) {
      .encolher:hover { background: rgba(255, 255, 255, 0.12); color: #fff; }
    }

    /* flex: 1 com min-height: 0 é o que permite a lista encolher e rolar
       dentro do pai, em vez de empurrar o que vem depois dela para fora. */
    nav {
      display: flex; flex-direction: column; gap: 2px;
      flex: 1; min-height: 0; overflow-y: auto;
      scrollbar-width: thin;
    }

    .item {
      display: flex; align-items: center; gap: 10px;
      padding: 8px 10px;
      min-height: 38px;
      border-radius: 9px;
      color: rgba(255, 255, 255, 0.76);
      text-decoration: none;
      font-size: 0.86rem; font-weight: 500;
      border: 1px solid transparent;
      transition: background-color 180ms ease, color 180ms ease;
      white-space: nowrap;
    }
    .item mat-icon { font-size: 19px; width: 19px; height: 19px; flex-shrink: 0; }

    /* Em tela sensível ao toque o alvo volta a 44px: dedo não tem a precisão
       do mouse, e é o tipo de ponteiro que decide isso, não a largura. */
    @media (pointer: coarse) {
      .item { min-height: 44px; }
    }

    @media (hover: hover) and (pointer: fine) {
      .item:hover { background: rgba(255, 255, 255, 0.07); color: #fff; }
    }

    /* O item atual: o lima marca onde você está. É o único lugar da lateral
       onde a cor cheia aparece, então não há dúvida sobre qual é. */
    .item.ativo {
      background: rgba(201, 169, 255, 0.14);
      border-color: rgba(201, 169, 255, 0.30);
      color: #fff;
    }
    .item.ativo mat-icon { color: var(--lima-400); }

    /* Encolhida: some o texto e o ícone vai para o centro. O nome reaparece
       como dica ao passar o mouse, então nada se perde. */
    .encolhida .rotulo { display: none; }
    .encolhida .item,
    .encolhida .pessoa { justify-content: center; padding-left: 8px; padding-right: 8px; }
    .encolhida .topo-lateral { flex-direction: column; gap: 10px; }
    .encolhida .marca { padding: 0; }

    /* ----------------------------------------------------- bloco da pessoa */
    /* Fino de propósito: é identificação, não navegação. Ocupar a largura
       toda faria parecer mais um item de menu, competindo com os de cima. */
    .pessoa {
      margin-top: 12px; flex-shrink: 0;
      display: flex; align-items: center; gap: 9px;
      width: fit-content; max-width: 100%; min-height: 44px;
      padding: 5px 10px 5px 6px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.10);
      background: rgba(255, 255, 255, 0.05);
      color: #fff; cursor: pointer; text-align: left;
      font-family: inherit;
      transition: background-color 180ms ease, border-color 180ms ease;
    }
    @media (hover: hover) and (pointer: fine) {
      .pessoa:hover { background: rgba(255, 255, 255, 0.10);
                      border-color: rgba(201, 169, 255, 0.28); }
    }

    .avatar {
      width: 30px; height: 30px; flex-shrink: 0;
      border-radius: 50%; overflow: hidden;
      display: flex; align-items: center; justify-content: center;
      background-image: linear-gradient(145deg, var(--lima-500) 0%, var(--verde-700) 100%);
      color: var(--petroleo-900); font-weight: 700; font-size: 0.85rem;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
    }
    .avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }

    .quem { display: flex; min-width: 0; }
    .quem .nome {
      font-size: 0.86rem; font-weight: 600; color: #fff;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }

    .seta { color: rgba(255, 255, 255, 0.5); font-size: 18px; width: 18px; height: 18px;
            margin-right: 2px; }

    /* ----------------------------------------------------- aviso de vigência */
    .faixa {
      display: flex; align-items: center; justify-content: center;
      gap: 8px; flex-wrap: wrap;
      padding: 10px 16px; font-size: 0.9rem; font-weight: 500;
      text-decoration: none; cursor: pointer;
    }
    .faixa strong { text-decoration: underline; }
    .faixa.vencida { background: var(--perigo-bg); color: var(--perigo); }
    .faixa.acabando { background: var(--alerta-bg); color: var(--alerta); }

    /* -------------------------------------------------------- celular */
    .barra-mobile { display: none; }
    .marca-mobile { display: flex; align-items: center; gap: 8px; font-weight: 500; }

    /* Abaixo de 960px a coluna lateral custa caro demais em largura: volta a
       barra de cima com menu sanduíche. */
    @media (max-width: 959px) {
      .estrutura, .estrutura.encolhida { grid-template-columns: 1fr; }
      .lateral { display: none; position: static; }
      .conteudo { grid-column: 1; }
      .barra-mobile { display: flex; }
    }
  `],
})
export class AppComponent implements OnInit {
  readonly auth = inject(AuthService);
  readonly assinatura = inject(AssinaturaService);
  readonly menu = MENU;

  readonly encolhida = signal<boolean>(this.lerPreferencia());

  /** A foto do Google não carregou. Mostra as iniciais no lugar. */
  readonly fotoFalhou = signal<boolean>(false);


  ngOnInit(): void {
    // Quem já chega logado precisa do papel e da vigência para a barra e a faixa.
    if (this.auth.logado()) {
      this.auth.me().subscribe({ error: () => undefined });
      this.assinatura.carregar().subscribe({ error: () => undefined });
    }
  }

  alternarBarra(): void {
    const novo = !this.encolhida();
    this.encolhida.set(novo);
    try {
      localStorage.setItem(CHAVE_ENCOLHIDA, novo ? '1' : '0');
    } catch {
      // Navegador com armazenamento bloqueado: a escolha vale só nesta visita.
    }
  }

  private lerPreferencia(): boolean {
    try {
      return localStorage.getItem(CHAVE_ENCOLHIDA) === '1';
    } catch {
      return false;
    }
  }
}
