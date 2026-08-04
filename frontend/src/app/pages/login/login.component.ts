import { Component, inject } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [MatCardModule, MatButtonModule, MatIconModule],
  template: `
    <div class="login-container">
      <mat-card class="login-card">
        <mat-card-content>
          <h1 class="marca">TáEmDia</h1>
          <p class="subtitulo">Cobrança automatizada e carteira de clientes</p>
          <button mat-raised-button color="primary" (click)="entrar()">
            <mat-icon>login</mat-icon>
            Continuar com Google
          </button>
          <p class="aviso">Acesso exclusivo via conta Google, sem senha.</p>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .login-container {
      display: flex; align-items: center; justify-content: center;
      min-height: 80vh; padding: 16px;
    }
    .login-card { max-width: 380px; width: 100%; text-align: center; padding: 24px; }
    .marca { margin: 0 0 4px; font-size: 2rem; color: #1565c0; }
    .subtitulo { margin: 0 0 24px; color: #555; }
    .aviso { margin-top: 16px; font-size: 0.8rem; color: #888; }
    button { width: 100%; }
  `],
})
export class LoginComponent {
  private auth = inject(AuthService);

  entrar(): void {
    this.auth.entrarComGoogle();
  }
}
