import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AssinaturaService, PagamentoPendente } from '../../core/assinatura.service';

/**
 * Conferência de comprovantes — visível apenas para quem está em ADMIN_EMAILS.
 *
 * Esconder a tela é conforto: quem não é administrador recebe 403 do servidor
 * mesmo chamando os endpoints direto.
 */
@Component({
  selector: 'app-assinaturas',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="pagina">
      <div class="cabecalho">
        <h2>Comprovantes</h2>
        <button mat-stroked-button (click)="carregar()" [disabled]="carregando()">
          <mat-icon>refresh</mat-icon> Atualizar
        </button>
      </div>
      <p class="ajuda">Confira o Pix recebido antes de liberar o acesso.</p>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else if (semAcesso()) {
        <mat-card class="bloco vazio-card">
          <mat-icon class="icone-grande">lock</mat-icon>
          <h3>Área restrita</h3>
          <p>Esta tela é da administração do sistema.</p>
        </mat-card>
      } @else if (pendentes().length === 0) {
        <mat-card class="bloco vazio-card">
          <mat-icon class="icone-grande">inbox</mat-icon>
          <h3>Nenhum comprovante aguardando</h3>
          <p>Quando alguém enviar um Pix, ele aparece aqui para conferência.</p>
        </mat-card>
      } @else {
        @for (p of pendentes(); track p.id) {
          <mat-card class="bloco item">
            <div class="quem">
              <div>
                <strong>{{ p.vendedor_nome || 'Sem nome' }}</strong>
                <span class="email">{{ p.vendedor_email }}</span>
              </div>
              <div class="valor">{{ dinheiro(p.valor) }}</div>
            </div>

            <div class="meta">
              <span><mat-icon inline>schedule</mat-icon> {{ dataHora(p.enviado_em) }}</span>
              <button mat-button (click)="abrir(p)">
                <mat-icon>visibility</mat-icon> Ver comprovante
              </button>
            </div>

            @if (recusando() === p.id) {
              <div class="recusa">
                <mat-form-field appearance="outline" class="campo">
                  <mat-label>Motivo da recusa</mat-label>
                  <input matInput [(ngModel)]="motivo" name="motivo"
                         placeholder="Ex.: valor diferente do combinado" />
                </mat-form-field>
                <button mat-button (click)="recusando.set(null)">Cancelar</button>
                <button mat-raised-button color="warn" (click)="confirmarRecusa(p)">
                  Confirmar recusa
                </button>
              </div>
            } @else {
              <div class="acoes">
                <button mat-button color="warn" (click)="pedirMotivo(p)">
                  <mat-icon>close</mat-icon> Recusar
                </button>
                <button mat-raised-button color="primary" [disabled]="agindo()"
                        (click)="aprovar(p)">
                  <mat-icon>check</mat-icon> Aprovar e liberar 30 dias
                </button>
              </div>
            }
          </mat-card>
        }
      }
    </div>
  `,
  styles: [`
    .pagina { max-width: 820px; margin: 0 auto; padding: 16px; }
    .cabecalho { display: flex; align-items: center; justify-content: space-between;
                 gap: 12px; flex-wrap: wrap; }
    .cabecalho h2 { margin: 0; }
    .ajuda { color: var(--texto-suave); margin-top: 4px; }
    .centro { display: flex; justify-content: center; padding: 32px; }
    .bloco { padding: 16px; margin-bottom: 16px; }

    .vazio-card { text-align: center; padding: 40px 20px; }
    .vazio-card h3 { margin: 12px 0 4px; }
    .vazio-card p { color: var(--texto-suave); margin: 0; }
    .icone-grande { font-size: 40px; width: 40px; height: 40px; color: var(--texto-fraco); }

    .quem { display: flex; align-items: flex-start; justify-content: space-between;
            gap: 12px; flex-wrap: wrap; }
    .quem > div:first-child { display: flex; flex-direction: column; }
    .email { font-size: 0.85rem; color: var(--texto-suave); }
    .valor { font-size: 1.3rem; font-weight: 600; color: var(--verde-800); }

    .meta { display: flex; align-items: center; justify-content: space-between;
            gap: 12px; flex-wrap: wrap; margin-top: 8px;
            font-size: 0.85rem; color: var(--texto-suave); }
    .meta span { display: flex; align-items: center; gap: 6px; }

    .acoes { display: flex; justify-content: flex-end; gap: 8px; flex-wrap: wrap;
             margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--borda); }
    .recusa { display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
              margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--borda); }
    .recusa .campo { flex: 1; min-width: 220px; }
  `],
})
export class AssinaturasComponent implements OnInit {
  private service = inject(AssinaturaService);
  private aviso = inject(MatSnackBar);

  readonly pendentes = signal<PagamentoPendente[]>([]);
  readonly carregando = signal<boolean>(true);
  readonly agindo = signal<boolean>(false);
  readonly semAcesso = signal<boolean>(false);
  readonly recusando = signal<string | null>(null);
  motivo = '';

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando.set(true);
    this.service.pendentes().subscribe({
      next: (lista) => {
        this.pendentes.set(lista);
        this.semAcesso.set(false);
        this.carregando.set(false);
      },
      error: (erro) => {
        this.semAcesso.set(erro.status === 403);
        this.carregando.set(false);
      },
    });
  }

  /** Abre o arquivo numa aba nova. Vem por endpoint autenticado, não por URL pública. */
  abrir(p: PagamentoPendente): void {
    this.service.baixarComprovante(p.id).subscribe({
      next: (arquivo) => {
        const url = URL.createObjectURL(arquivo);
        window.open(url, '_blank');
        // Só revoga depois que a aba teve tempo de carregar.
        setTimeout(() => URL.revokeObjectURL(url), 60_000);
      },
      error: () => this.aviso.open('Não foi possível abrir o comprovante.', 'OK',
                                   { duration: 4000 }),
    });
  }

  aprovar(p: PagamentoPendente): void {
    this.agindo.set(true);
    this.service.aprovar(p.id).subscribe({
      next: () => {
        this.agindo.set(false);
        this.aviso.open(`Acesso de ${p.vendedor_nome} liberado por 30 dias.`, 'OK',
                        { duration: 4000 });
        this.carregar();
      },
      error: (erro) => {
        this.agindo.set(false);
        this.aviso.open(erro.error?.detail ?? 'Não foi possível aprovar.', 'OK',
                        { duration: 4000 });
      },
    });
  }

  pedirMotivo(p: PagamentoPendente): void {
    this.motivo = '';
    this.recusando.set(p.id);
  }

  confirmarRecusa(p: PagamentoPendente): void {
    if (this.motivo.trim().length < 3) {
      this.aviso.open('Escreva o motivo — a pessoa vai ler.', 'OK', { duration: 3000 });
      return;
    }
    this.service.recusar(p.id, this.motivo.trim()).subscribe({
      next: () => {
        this.recusando.set(null);
        this.aviso.open('Comprovante recusado.', 'OK', { duration: 3000 });
        this.carregar();
      },
      error: (erro) => this.aviso.open(erro.error?.detail ?? 'Não foi possível recusar.', 'OK',
                                       { duration: 4000 }),
    });
  }

  dinheiro(v: number): string { return 'R$ ' + v.toFixed(2).replace('.', ','); }
  dataHora(iso: string): string {
    const dt = new Date(iso);
    return dt.toLocaleDateString('pt-BR') + ', ' +
           dt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }
}
