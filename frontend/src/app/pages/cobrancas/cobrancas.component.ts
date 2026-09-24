import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { CobrancaLog, CobrancasService } from '../../core/cobrancas.service';

type Periodo = 'hoje' | 'semana' | 'mes';

const ROTULO_TIPO: Record<string, string> = {
  lembrete: 'Lembrete',
  vencimento: 'Vence hoje',
  atraso: 'Atraso',
  manual: 'Manual',
  resumo: 'Resumo diário',
};

@Component({
  selector: 'app-cobrancas',
  standalone: true,
  imports: [
    MatCardModule, MatButtonModule, MatIconModule, MatTabsModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="pagina">
      <h2>Cobranças</h2>
      <p class="ajuda">Histórico das mensagens enviadas pelo sistema.</p>

      <mat-tab-group (selectedTabChange)="trocarPeriodo($event.index)">
        <mat-tab label="Hoje"></mat-tab>
        <mat-tab label="Semana"></mat-tab>
        <mat-tab label="Mês"></mat-tab>
      </mat-tab-group>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else if (logs().length === 0) {
        <p class="vazio">Nenhuma cobrança enviada neste período.</p>
      } @else {
        @for (l of logs(); track l.id) {
          <mat-card class="item">
            <div class="topo">
              <span class="cliente" (click)="abrirPerfil(l)">
                <mat-icon inline>{{ l.tipo === 'resumo' ? 'summarize' : 'person' }}</mat-icon>
                {{ l.cliente_nome }}
              </span>
              <span class="direita">
                <span class="etiqueta" [class]="'tipo-' + l.tipo">{{ rotulo(l.tipo) }}</span>
                <span class="status" [class.falhou]="l.status !== 'enviado'">
                  {{ l.status === 'enviado' ? 'Enviada' : 'Na fila' }}
                </span>
              </span>
            </div>
            <p class="mensagem">{{ l.conteudo }}</p>
            <span class="data">{{ formatarData(l.criado_em) }}</span>
          </mat-card>
        }
      }
    </div>
  `,
  styles: [`
    .pagina { max-width: 760px; margin: 0 auto; padding: 16px; }
    .ajuda { color: var(--texto-suave); margin-bottom: 8px; }
    .centro { display: flex; justify-content: center; padding: 32px; }
    .vazio { text-align: center; color: var(--texto-fraco); padding: 32px; }
    .item { padding: 14px 16px; margin: 12px 0; }
    .topo { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
    .cliente { font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px; }

    .direita { display: flex; align-items: center; gap: 8px; }
    .etiqueta { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; background: var(--borda); color: var(--texto); }
    .tipo-atraso { background: var(--perigo-bg); color: var(--perigo); }
    .tipo-lembrete { background: var(--info-bg); color: var(--verde-800); }
    .tipo-vencimento { background: var(--alerta-bg); color: var(--alerta); }
    .tipo-manual { background: var(--verde-50); color: var(--verde-700); }
    .tipo-resumo { background: var(--sucesso-bg); color: var(--sucesso); }
    .status { font-size: 0.75rem; color: var(--sucesso); }
    .status.falhou { color: var(--alerta); }
    .mensagem { white-space: pre-wrap; color: var(--texto); font-size: 0.88rem; margin: 8px 0 4px; }
    .data { font-size: 0.72rem; color: var(--texto-fraco); }
  `],
})
export class CobrancasComponent implements OnInit {
  private service = inject(CobrancasService);
  private router = inject(Router);
  private snack = inject(MatSnackBar);

  readonly logs = signal<CobrancaLog[]>([]);
  readonly carregando = signal<boolean>(true);
  private periodo: Periodo = 'hoje';

  ngOnInit(): void { this.carregar(); }

  trocarPeriodo(indice: number): void {
    this.periodo = (['hoje', 'semana', 'mes'] as Periodo[])[indice] ?? 'hoje';
    this.carregar();
  }

  private carregar(): void {
    this.carregando.set(true);
    this.service.listar(this.periodo).subscribe({
      next: (lista) => { this.logs.set(lista); this.carregando.set(false); },
      error: () => { this.carregando.set(false); this.snack.open('Erro ao carregar as cobranças.', 'OK', { duration: 4000 }); },
    });
  }

  abrirPerfil(l: CobrancaLog): void {
    if (l.cliente_id) this.router.navigate(['/clientes', l.cliente_id]);
  }

  rotulo(tipo: string): string { return ROTULO_TIPO[tipo] ?? tipo; }

  formatarData(iso: string): string {
    const d = new Date(iso + (iso.endsWith('Z') ? '' : 'Z'));
    return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  }
}
