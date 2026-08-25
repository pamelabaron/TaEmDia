import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Ranking, RankingCliente, RankingService } from '../../core/ranking.service';

const ROTULO: Record<string, string> = {
  bom: 'Bom pagador',
  regular: 'Pagador regular',
  inadimplente: 'Inadimplente',
  sem_historico: 'Sem histórico',
};

@Component({
  selector: 'app-ranking',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatIconModule, MatFormFieldModule,
    MatSelectModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="pagina">
      <div class="cabecalho">
        <h2>Ranking de pagadores</h2>
        <mat-form-field appearance="outline" class="periodo">
          <mat-label>Período</mat-label>
          <mat-select [(ngModel)]="meses" (selectionChange)="carregar()">
            <mat-option [value]="3">Últimos 3 meses</mat-option>
            <mat-option [value]="6">Últimos 6 meses</mat-option>
            <mat-option [value]="12">Últimos 12 meses</mat-option>
          </mat-select>
        </mat-form-field>
      </div>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        @if (dados(); as d) {
          <div class="cards">
            <mat-card class="card bom">
              <mat-icon>sentiment_very_satisfied</mat-icon>
              <span class="num">{{ d.bons }}</span>
              <span class="rot">Bons pagadores</span>
            </mat-card>
            <mat-card class="card regular">
              <mat-icon>sentiment_neutral</mat-icon>
              <span class="num">{{ d.regulares }}</span>
              <span class="rot">Pagadores regulares</span>
            </mat-card>
            <mat-card class="card inadimplente">
              <mat-icon>sentiment_very_dissatisfied</mat-icon>
              <span class="num">{{ d.inadimplentes }}</span>
              <span class="rot">Inadimplentes</span>
            </mat-card>
          </div>

          <mat-card class="lista">
            @if (d.clientes.length === 0) {
              <p class="vazio">Nenhum cliente cadastrado ainda.</p>
            } @else {
              @for (c of d.clientes; track c.id) {
                <div class="linha clicavel" (click)="abrirPerfil(c.id)">
                  <div class="info">
                    <span class="nome">{{ c.nome }}</span>
                    <span class="tag" [class]="c.classificacao">{{ rotulo(c.classificacao) }}</span>
                  </div>
                  <div class="barra-wrap" [title]="c.percentual_em_dia + '% das parcelas pagas em dia'">
                    <div class="barra" [class]="c.classificacao" [style.width.%]="c.percentual_em_dia"></div>
                  </div>
                  <span class="perc">{{ c.total_avaliadas > 0 ? c.percentual_em_dia + '%' : '—' }}</span>
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
    .cabecalho { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; }
    .cabecalho h2 { margin: 0; }
    .periodo { width: 200px; }
    .centro { display: flex; justify-content: center; padding: 32px; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 16px; }
    .card { display: flex; flex-direction: column; align-items: center; padding: 16px; }
    .card mat-icon { font-size: 36px; height: 36px; width: 36px; }
    .card .num { font-size: 2rem; font-weight: 700; }
    .card .rot { color: #666; font-size: 0.85rem; }
    .card.bom { color: #2e7d32; } .card.regular { color: #f9a825; } .card.inadimplente { color: #c62828; }
    .lista { padding: 8px 16px; }
    .linha { display: flex; align-items: center; gap: 12px; padding: 12px 4px; border-bottom: 1px solid #eee; }
    .info { min-width: 180px; display: flex; flex-direction: column; gap: 4px; }
    .nome { font-weight: 500; }
    .tag { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; width: fit-content; color: #fff; }
    .tag.bom { background: #2e7d32; } .tag.regular { background: #f9a825; }
    .tag.inadimplente { background: #c62828; } .tag.sem_historico { background: #9e9e9e; }
    .barra-wrap { flex: 1; height: 10px; background: #eee; border-radius: 5px; overflow: hidden; }
    .barra { height: 100%; border-radius: 5px; }
    .barra.bom { background: #2e7d32; } .barra.regular { background: #f9a825; }
    .barra.inadimplente { background: #c62828; } .barra.sem_historico { background: #bdbdbd; }
    .perc { width: 44px; text-align: right; font-size: 0.85rem; color: #555; }
    .vazio { text-align: center; color: #888; padding: 24px; }
    .clicavel { cursor: pointer; } .clicavel:hover { background: #f5f5f5; }
  `],
})
export class RankingComponent implements OnInit {
  private service = inject(RankingService);
  private router = inject(Router);

  readonly dados = signal<Ranking | null>(null);
  readonly carregando = signal<boolean>(true);
  meses = 12;

  ngOnInit(): void { this.carregar(); }

  carregar(): void {
    this.carregando.set(true);
    this.service.carregar(this.meses).subscribe({
      next: (d) => { this.dados.set(d); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  rotulo(c: string): string { return ROTULO[c] ?? c; }
  abrirPerfil(id: string): void { this.router.navigate(['/clientes', id]); }
}
