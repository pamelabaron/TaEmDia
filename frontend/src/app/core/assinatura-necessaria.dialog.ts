import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

/**
 * Mostrado quando o servidor recusa uma gravação com 402.
 *
 * É um diálogo, e não um aviso de rodapé, por dois motivos: os componentes têm
 * os próprios avisos genéricos de erro e um sobrescreveria o outro; e pedir
 * assinatura é uma decisão, não uma notificação de passagem.
 */
@Component({
  selector: 'app-assinatura-necessaria',
  standalone: true,
  imports: [MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <div class="cabecalho">
      <mat-icon>lock</mat-icon>
      <h2 mat-dialog-title>Assinatura necessária</h2>
    </div>

    <mat-dialog-content>
      <p>{{ data.mensagem }}</p>
      <p class="detalhe">
        Você continua vendo seus clientes, parcelas e relatórios normalmente. O que fica
        parado é cadastrar, cobrar e conectar o WhatsApp.
      </p>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Agora não</button>
      <button mat-raised-button color="primary" (click)="irParaAssinatura()">
        Ver minha assinatura
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    .cabecalho { display: flex; align-items: center; gap: 10px; padding: 20px 24px 0; }
    .cabecalho mat-icon { color: var(--alerta); }
    .cabecalho h2 { margin: 0; padding: 0; }
    p { margin: 0 0 10px; }
    .detalhe { color: var(--texto-suave); font-size: 0.9rem; margin-bottom: 0; }
  `],
})
export class AssinaturaNecessariaDialog {
  readonly data = inject<{ mensagem: string }>(MAT_DIALOG_DATA);
  private ref = inject(MatDialogRef<AssinaturaNecessariaDialog>);
  private router = inject(Router);

  irParaAssinatura(): void {
    this.ref.close();
    this.router.navigate(['/configuracoes'], { fragment: 'assinatura' });
  }
}
