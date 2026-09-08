import { Component, inject } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { AuthService } from './core/auth.service';

interface ItemMenu { rota: string; titulo: string; icone: string; }

const MENU: ItemMenu[] = [
  { rota: '/painel', titulo: 'Painel', icone: 'dashboard' },
  { rota: '/clientes', titulo: 'Clientes', icone: 'people' },
  { rota: '/ranking', titulo: 'Ranking', icone: 'leaderboard' },
  { rota: '/cobrancas', titulo: 'Cobranças', icone: 'send' },
  { rota: '/mensagens', titulo: 'Mensagens', icone: 'chat' },
  { rota: '/configuracoes', titulo: 'Configurações', icone: 'settings' },
];

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet, RouterLink, RouterLinkActive,
    MatToolbarModule, MatButtonModule, MatIconModule, MatMenuModule,
  ],
  template: `
    <!-- A barra só aparece depois do login: a página de apresentação tem
         o cabeçalho próprio dela. -->
    @if (auth.logado()) {
      <mat-toolbar color="primary">
        <!-- Celular: menu sanduíche -->
        <button mat-icon-button class="so-mobile" [matMenuTriggerFor]="menuMobile" aria-label="Abrir menu">
          <mat-icon>menu</mat-icon>
        </button>
        <mat-menu #menuMobile="matMenu">
          @for (item of menu; track item.rota) {
            <a mat-menu-item [routerLink]="item.rota">
              <mat-icon>{{ item.icone }}</mat-icon>
              <span>{{ item.titulo }}</span>
            </a>
          }
          <a mat-menu-item (click)="auth.sair()">
            <mat-icon>logout</mat-icon>
            <span>Sair</span>
          </a>
        </mat-menu>

        <span class="marca"><mat-icon>task_alt</mat-icon> TáEmDia</span>

        <!-- Computador: menu na barra -->
        <nav class="so-desktop">
          @for (item of menu; track item.rota) {
            <a mat-button [routerLink]="item.rota" routerLinkActive="ativo">{{ item.titulo }}</a>
          }
        </nav>

        <span class="espaco"></span>

        <button mat-button class="so-desktop" (click)="auth.sair()">
          <mat-icon>logout</mat-icon>
          Sair
        </button>
      </mat-toolbar>
    }
    <router-outlet></router-outlet>
  `,
  styles: [`
    .marca {
      display: flex; align-items: center; gap: 8px;
      font-weight: 500; margin-right: 24px;
    }
    .espaco { flex: 1 1 auto; }
    nav a { margin-right: 4px; }
    .ativo { background: rgba(255, 255, 255, 0.18); }

    /* Por padrão (computador): esconde o menu sanduíche. */
    .so-mobile { display: none; }

    /* Telas estreitas (celular): troca o menu da barra pelo sanduíche. */
    @media (max-width: 860px) {
      .so-desktop { display: none; }
      .so-mobile { display: inline-flex; }
      .marca { margin-right: 8px; }
    }
  `],
})
export class AppComponent {
  readonly auth = inject(AuthService);
  readonly menu = MENU;
}
