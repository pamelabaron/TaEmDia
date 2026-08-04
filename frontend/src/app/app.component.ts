import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from './core/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, MatToolbarModule, MatButtonModule, MatIconModule],
  template: `
    <mat-toolbar color="primary">
      <span class="marca">TáEmDia</span>
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
    .marca { font-weight: 500; }
    .espaco { flex: 1 1 auto; }
  `],
})
export class AppComponent {
  readonly auth = inject(AuthService);
}
