import { Component, inject } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from './core/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, MatToolbarModule, MatButtonModule, MatIconModule],
  template: `
    <mat-toolbar color="primary">
      <span class="marca">TáEmDia</span>
      @if (auth.logado()) {
        <nav>
          <a mat-button routerLink="/painel" routerLinkActive="ativo">Painel</a>
          <a mat-button routerLink="/clientes" routerLinkActive="ativo">Clientes</a>
          <a mat-button routerLink="/mensagens" routerLinkActive="ativo">Mensagens</a>
        </nav>
      }
      <span class="espaco"></span>
      @if (auth.logado()) {
        <button mat-button (click)="auth.sair()">
          <mat-icon>logout</mat-icon>
          Sair
        </button>
      }
    </mat-toolbar>
    <router-outlet></router-outlet>
  `,
  styles: [`
    .marca { font-weight: 500; margin-right: 24px; }
    .espaco { flex: 1 1 auto; }
    nav a { margin-right: 4px; }
    .ativo { background: rgba(255,255,255,0.15); }
  `],
})
export class AppComponent {
  readonly auth = inject(AuthService);
}
