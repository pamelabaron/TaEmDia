import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../core/auth.service';
import { AssinaturaService } from '../../core/assinatura.service';

@Component({
  selector: 'app-callback',
  standalone: true,
  imports: [MatProgressSpinnerModule],
  template: `
    <div class="callback">
      <mat-spinner diameter="40"></mat-spinner>
      <p>Entrando…</p>
    </div>
  `,
  styles: [`
    .callback {
      display: flex; flex-direction: column; align-items: center;
      justify-content: center; min-height: 60vh; gap: 16px; color: #555;
    }
  `],
})
export class CallbackComponent implements OnInit {
  private auth = inject(AuthService);
  private assinatura = inject(AssinaturaService);
  private router = inject(Router);

  ngOnInit(): void {
    // O backend redireciona para cá com o token no fragmento: /auth/callback#token=XXX
    const fragmento = window.location.hash.replace(/^#/, '');
    const params = new URLSearchParams(fragmento);
    const token = params.get('token');
    if (token) {
      this.auth.salvarToken(token);
      // Carrega papel e vigência antes de entrar: a barra e a faixa dependem disso.
      this.auth.me().subscribe({ error: () => undefined });
      this.assinatura.carregar().subscribe({ error: () => undefined });
      this.router.navigate(['/painel']);
    } else {
      this.router.navigate(['/login']);
    }
  }
}
