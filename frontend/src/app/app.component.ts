import { Component, OnInit, inject } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
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
  { rota: '/configuracoes', titulo: 'Configurações', icone: 'tune' },
];

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet, RouterLink, RouterLinkActive,
    MatToolbarModule, MatButtonModule, MatIconModule, MatMenuModule,
  ],
  template: `
    @if (auth.logado()) {
      <div class="estrutura">

        <!-- ============================================ navegação lateral
             No computador a navegação fica na lateral: cabe ícone e rótulo
             lado a lado, e o menu não compete com o título da página.
             No celular ela vira a barra de cima com menu sanduíche — uma
             coluna fixa comeria metade de uma tela de 375px. -->
        <aside class="lateral">
          <a class="marca" routerLink="/painel">
            <mat-icon>task_alt</mat-icon>
            <span>TáEmDia</span>
          </a>

          <nav>
            @for (item of menu; track item.rota) {
              <a [routerLink]="item.rota" routerLinkActive="ativo" class="item">
                <mat-icon>{{ item.icone }}</mat-icon>
                <span>{{ item.titulo }}</span>
              </a>
            }
            @if (auth.administrador()) {
              <a routerLink="/assinaturas" routerLinkActive="ativo" class="item">
                <mat-icon>receipt_long</mat-icon>
                <span>Comprovantes</span>
              </a>
            }
          </nav>

          <button class="item sair" (click)="auth.sair()">
            <mat-icon>logout</mat-icon>
            <span>Sair</span>
          </button>
        </aside>

        <!-- ================================================ barra do celular -->
        <mat-toolbar color="primary" class="barra-mobile">
          <button mat-icon-button [matMenuTriggerFor]="menuMobile" aria-label="Abrir menu">
            <mat-icon>menu</mat-icon>
          </button>
          <mat-menu #menuMobile="matMenu">
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
            <a mat-menu-item (click)="auth.sair()">
              <mat-icon>logout</mat-icon>
              <span>Sair</span>
            </a>
          </mat-menu>

          <span class="marca-mobile"><mat-icon>task_alt</mat-icon> TáEmDia</span>
        </mat-toolbar>

        <!-- ==================================================== conteúdo -->
        <main class="conteudo">
          <!-- Aviso de vigência. Aparece só quando há o que avisar: sistema
               que avisa o tempo todo deixa de ser lido. -->
          @if (assinatura.bloqueada()) {
            <a class="faixa vencida" routerLink="/configuracoes" fragment="assinatura">
              <mat-icon inline>lock</mat-icon>
              Sua assinatura venceu. Você continua vendo tudo, mas não consegue cadastrar nem
              cobrar. <strong>Renovar</strong>
            </a>
          } @else {
            @if (assinatura.acabando(); as dias) {
              <a class="faixa acabando" routerLink="/configuracoes" fragment="assinatura">
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
    .conteudo {
      min-width: 0; /* sem isto, conteúdo largo empurra a lateral */
      /* Sem a barra de cima, o título encostava na borda. O respiro maior em
         cima do que embaixo é o que faz o cabeçalho pertencer ao conteúdo que
         vem depois dele, e não flutuar. */
      padding-top: 14px;
    }
    @media (max-width: 959px) { .conteudo { padding-top: 0; } }

    /* -------------------------------------------------------- barra lateral */
    .lateral {
      position: sticky; top: 0; align-self: start;
      height: 100dvh;
      display: flex; flex-direction: column;
      padding: 20px 14px 18px;
      background-color: var(--petroleo-900);
      background-image:
        radial-gradient(20rem 16rem at 8% 100%, rgba(168, 227, 74, 0.30), transparent 66%),
        radial-gradient(22rem 18rem at 100% 0%, rgba(60, 182, 118, 0.34), transparent 62%),
        linear-gradient(168deg, var(--petroleo-800) 0%, var(--petroleo-900) 100%);
      box-shadow: inset -1px 0 0 rgba(168, 227, 74, 0.14);
    }

    .marca {
      display: flex; align-items: center; gap: 10px;
      padding: 6px 12px 0;
      color: #fff; text-decoration: none;
      font-family: "Outfit", sans-serif;
      font-weight: 600; font-size: 1.2rem; letter-spacing: -0.02em;
      margin-bottom: 26px;
    }
    .marca mat-icon { color: var(--lima-400); }

    nav { display: flex; flex-direction: column; gap: 3px; }

    .item {
      display: flex; align-items: center; gap: 12px;
      padding: 11px 12px;
      min-height: 44px;
      border-radius: 10px;
      color: rgba(255, 255, 255, 0.76);
      text-decoration: none;
      font-size: 0.94rem; font-weight: 500;
      border: 1px solid transparent;
      transition: background-color 180ms ease, color 180ms ease;
    }
    .item mat-icon { font-size: 21px; width: 21px; height: 21px; }

    @media (hover: hover) and (pointer: fine) {
      .item:hover { background: rgba(255, 255, 255, 0.07); color: #fff; }
    }

    /* O item atual: o lima marca onde você está. É o único lugar da lateral
       onde a cor cheia aparece, então não há dúvida sobre qual é. */
    .item.ativo {
      background: rgba(168, 227, 74, 0.14);
      border-color: rgba(168, 227, 74, 0.30);
      color: #fff;
    }
    .item.ativo mat-icon { color: var(--lima-400); }

    /* "Sair" desce para o rodapé da coluna, longe da navegação: é saída, não
       destino. */
    .sair {
      margin-top: auto;
      width: 100%;
      background: none; border: 1px solid transparent;
      font-family: inherit; cursor: pointer; text-align: left;
    }

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
      .estrutura { grid-template-columns: 1fr; }
      .lateral { display: none; }
      .barra-mobile { display: flex; }
    }
  `],
})
export class AppComponent implements OnInit {
  readonly auth = inject(AuthService);
  readonly assinatura = inject(AssinaturaService);
  readonly menu = MENU;

  ngOnInit(): void {
    // Quem já chega logado precisa do papel e da vigência para a barra e a faixa.
    if (this.auth.logado()) {
      this.auth.me().subscribe({ error: () => undefined });
      this.assinatura.carregar().subscribe({ error: () => undefined });
    }
  }
}
