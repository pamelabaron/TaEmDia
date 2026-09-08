import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Dashboard, DashboardService } from '../../core/dashboard.service';

interface Barra { label: string; valor: number; altura: number; }

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [MatCardModule, MatIconModule, MatProgressSpinnerModule, MatButtonModule],
  template: `
    <div class="pagina">
      <div class="cabecalho">
        <h2>Painel</h2>
        <button mat-stroked-button (click)="exportarPdf()" [disabled]="exportando()">
          <mat-icon>picture_as_pdf</mat-icon> Exportar PDF
        </button>
      </div>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        @if (dados(); as d) {
        <div class="kpis">
          <mat-card class="kpi receber">
            <span class="rotulo">Total a receber</span>
            <span class="valor">{{ dinheiro(d.total_a_receber) }}</span>
          </mat-card>
          <mat-card class="kpi recebido">
            <span class="rotulo">Recebido no mês</span>
            <span class="valor">{{ dinheiro(d.recebido_no_mes) }}</span>
          </mat-card>
          <mat-card class="kpi atraso">
            <span class="rotulo">Em atraso</span>
            <span class="valor">{{ dinheiro(d.em_atraso) }}</span>
          </mat-card>
          <mat-card class="kpi inadimplentes">
            <span class="rotulo">Clientes inadimplentes</span>
            <span class="valor">{{ d.clientes_inadimplentes }}</span>
          </mat-card>
        </div>

        <mat-card class="bloco">
          <h3>Recebimentos por mês</h3>
          @if (barras().length === 0) {
            <p class="vazio">Ainda não há pagamentos registrados.</p>
          } @else {
            <div class="grafico">
              @for (b of barras(); track b.label) {
                <div class="coluna">
                  <span class="cifra">{{ dinheiro(b.valor) }}</span>
                  <div class="barra" [style.height.%]="b.altura"></div>
                  <span class="mes">{{ b.label }}</span>
                </div>
              }
            </div>
          }
        </mat-card>

        <mat-card class="bloco">
          <h3>Clientes em atraso</h3>
          @if (d.clientes_em_atraso.length === 0) {
            <p class="vazio">Nenhum cliente em atraso. 🎉</p>
          } @else {
            @for (c of d.clientes_em_atraso; track c.id) {
              <div class="linha-atraso clicavel" (click)="abrirPerfil(c.id)">
                <span><mat-icon>person</mat-icon> {{ c.nome }}</span>
                <span class="valor-atraso">{{ dinheiro(c.valor_atrasado) }}</span>
              </div>
            }
          }
        </mat-card>
        }
      }
    </div>
  `,
  styles: [`
    .pagina { max-width: 820px; margin: 0 auto; padding: 16px; }
    .cabecalho { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
    .cabecalho h2 { margin: 0; }
    .centro { display: flex; justify-content: center; padding: 32px; }
    .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 16px; }
    .kpi { display: flex; flex-direction: column; padding: 16px; border-left: 4px solid var(--verde-800); }
    .kpi .rotulo { font-size: 0.8rem; color: var(--texto-suave); }
    .kpi .valor { font-size: 1.5rem; font-weight: 600; margin-top: 4px; }
    .kpi.receber { border-color: var(--verde-800); } .kpi.receber .valor { color: var(--verde-800); }
    .kpi.recebido { border-color: var(--sucesso); } .kpi.recebido .valor { color: var(--sucesso); }
    .kpi.atraso { border-color: var(--alerta); } .kpi.atraso .valor { color: var(--alerta); }
    .kpi.inadimplentes { border-color: var(--perigo); } .kpi.inadimplentes .valor { color: var(--perigo); }
    .bloco { padding: 16px; margin-bottom: 16px; }
    .bloco h3 { margin: 0 0 16px; }
    .grafico { display: flex; align-items: flex-end; gap: 16px; height: 160px; padding-top: 20px; }
    .coluna { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; flex: 1; height: 100%; }
    .cifra { font-size: 0.7rem; color: var(--texto-suave); margin-bottom: 4px; }
    .barra { width: 70%; max-width: 48px; background: var(--sucesso); border-radius: 4px 4px 0 0; min-height: 2px; transition: height .3s; }
    .mes { font-size: 0.75rem; color: var(--texto-suave); margin-top: 6px; }
    .vazio { color: var(--texto-fraco); }
    .linha-atraso { display: flex; justify-content: space-between; align-items: center; padding: 10px 4px; border-bottom: 1px solid var(--borda); }
    .linha-atraso span { display: flex; align-items: center; gap: 6px; }
    .valor-atraso { color: var(--perigo); font-weight: 500; }
    .clicavel { cursor: pointer; }
  `],
})
export class DashboardComponent implements OnInit {
  private service = inject(DashboardService);
  private router = inject(Router);
  private snack = inject(MatSnackBar);

  readonly dados = signal<Dashboard | null>(null);
  readonly carregando = signal<boolean>(true);
  readonly exportando = signal<boolean>(false);

  readonly barras = computed<Barra[]>(() => {
    const d = this.dados();
    if (!d || d.recebimentos_mensais.length === 0) return [];
    const max = Math.max(...d.recebimentos_mensais.map((r) => r.total), 1);
    return d.recebimentos_mensais.map((r) => ({
      label: this.rotuloMes(r.mes),
      valor: r.total,
      altura: (r.total / max) * 100,
    }));
  });

  ngOnInit(): void {
    this.service.carregar().subscribe({
      next: (d) => { this.dados.set(d); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  exportarPdf(): void {
    this.exportando.set(true);
    this.service.exportarPdf().subscribe({
      next: (arquivo) => {
        this.exportando.set(false);
        this.baixar(arquivo);
      },
      error: () => {
        this.exportando.set(false);
        this.snack.open('Não foi possível gerar o relatório.', 'OK', { duration: 4000 });
      },
    });
  }

  /** Entrega o arquivo ao navegador para download. */
  private baixar(arquivo: Blob): void {
    const url = URL.createObjectURL(arquivo);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'taemdia-relatorio.pdf';
    link.click();
    URL.revokeObjectURL(url);
  }

  abrirPerfil(id: string): void { this.router.navigate(['/clientes', id]); }
  dinheiro(v: number): string { return 'R$ ' + v.toFixed(2).replace('.', ','); }
  rotuloMes(m: string): string { const [a, mes] = m.split('-'); return `${MESES[+mes - 1]}/${a.slice(2)}`; }
}
