import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { PerfilCliente, VendasService } from '../../core/vendas.service';

@Component({
  selector: 'app-cliente-perfil',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="pagina">
      <button mat-button (click)="voltar()"><mat-icon>arrow_back</mat-icon> Voltar</button>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        @if (perfil(); as p) {
        <div class="topo">
          <div>
            <h2>{{ p.nome }}</h2>
            <p class="whats"><mat-icon>chat</mat-icon> {{ p.whatsapp_numero }}</p>
          </div>
          <mat-card class="saldo" [class.zerado]="p.saldo_devedor === 0">
            <span class="rotulo">Saldo devedor</span>
            <span class="valor">{{ dinheiro(p.saldo_devedor) }}</span>
          </mat-card>
        </div>

        <div class="acoes">
          <button mat-raised-button color="primary" (click)="alternarForm()">
            <mat-icon>{{ mostrarForm() ? 'close' : 'add_shopping_cart' }}</mat-icon>
            {{ mostrarForm() ? 'Cancelar' : 'Nova venda' }}
          </button>
        </div>

        @if (mostrarForm()) {
          <mat-card class="form-card">
            <mat-card-content>
              <mat-form-field appearance="outline" class="campo">
                <mat-label>Valor total (R$)</mat-label>
                <input matInput type="number" min="1" step="0.01" [(ngModel)]="nova.valor_total" name="valor" />
              </mat-form-field>
              <mat-form-field appearance="outline" class="campo">
                <mat-label>Número de parcelas (1 a 60)</mat-label>
                <input matInput type="number" min="1" max="60" [(ngModel)]="nova.num_parcelas" name="num" />
              </mat-form-field>
              <mat-form-field appearance="outline" class="campo">
                <mat-label>Data da 1ª parcela</mat-label>
                <input matInput type="date" [(ngModel)]="nova.data_primeira_parcela" name="data" />
              </mat-form-field>
              <button mat-raised-button color="primary" [disabled]="salvando()" (click)="salvarVenda()">
                Registrar venda
              </button>
            </mat-card-content>
          </mat-card>
        }

        <h3>Vendas</h3>
        @if (p.vendas.length === 0) {
          <p class="vazio">Nenhuma venda registrada.</p>
        } @else {
          @for (v of p.vendas; track v.id) {
            <mat-card class="venda-card" [class.cancelada]="v.status === 'cancelada'">
              <div class="venda-topo">
                <div>
                  <strong>{{ dinheiro(v.valor_total) }}</strong> em {{ v.num_parcelas }}x
                  @if (v.status === 'cancelada') { <span class="tag-cancelada">CANCELADA</span> }
                </div>
                @if (v.status === 'ativa') {
                  <button mat-button color="warn" (click)="cancelar(v.id)">
                    <mat-icon>delete_outline</mat-icon> Cancelar venda
                  </button>
                }
              </div>
              <table class="parcelas">
                <tr>
                  <th>#</th><th>Valor</th><th>Vencimento</th><th>Situação</th><th></th>
                </tr>
                @for (parc of v.parcelas; track parc.id) {
                  <tr>
                    <td>{{ parc.numero_parcela }}</td>
                    <td>{{ dinheiro(parc.valor) }}</td>
                    <td>{{ data(parc.data_vencimento) }}</td>
                    <td><span class="chip {{ parc.status }}">{{ rotuloStatus(parc.status) }}</span></td>
                    <td>
                      @if (parc.status !== 'paga' && v.status === 'ativa') {
                        <button mat-button color="primary" (click)="pagar(parc.id)">Marcar como pago</button>
                      }
                    </td>
                  </tr>
                }
              </table>
            </mat-card>
          }
        }
        }
      }
    </div>
  `,
  styles: [`
    .pagina { max-width: 760px; margin: 0 auto; padding: 16px; }
    .topo { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
    .topo h2 { margin: 8px 0 4px; }
    .whats { display: flex; align-items: center; gap: 6px; color: #555; margin: 0; }
    .whats mat-icon { font-size: 18px; height: 18px; width: 18px; }
    .saldo { display: flex; flex-direction: column; padding: 12px 20px; text-align: right; background: #fff3e0; }
    .saldo.zerado { background: #e8f5e9; }
    .saldo .rotulo { font-size: 0.75rem; color: #777; }
    .saldo .valor { font-size: 1.6rem; font-weight: 600; color: #e65100; }
    .saldo.zerado .valor { color: #2e7d32; }
    .acoes { margin: 16px 0; }
    .form-card, .venda-card { margin-bottom: 16px; }
    .campo { width: 100%; }
    .venda-topo { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
    .venda-card.cancelada { opacity: 0.6; }
    .tag-cancelada { color: #c62828; font-size: 0.75rem; margin-left: 8px; }
    table.parcelas { width: 100%; border-collapse: collapse; }
    table.parcelas th, table.parcelas td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
    .chip { padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 500; }
    .chip.paga { background: #e8f5e9; color: #2e7d32; }
    .chip.atrasada { background: #ffebee; color: #c62828; }
    .chip.pendente { background: #e3f2fd; color: #1565c0; }
    .chip.aguardando_confirmacao { background: #fff8e1; color: #ef6c00; }
    .centro { display: flex; justify-content: center; padding: 32px; }
    .vazio { color: #888; }
  `],
})
export class ClientePerfilComponent implements OnInit {
  private service = inject(VendasService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private snack = inject(MatSnackBar);

  readonly perfil = signal<PerfilCliente | null>(null);
  readonly carregando = signal<boolean>(true);
  readonly mostrarForm = signal<boolean>(false);
  readonly salvando = signal<boolean>(false);
  private clienteId = '';
  nova = { valor_total: null as number | null, num_parcelas: 1, data_primeira_parcela: '' };

  ngOnInit(): void {
    this.clienteId = this.route.snapshot.paramMap.get('id') ?? '';
    this.carregar();
  }

  private carregar(): void {
    this.carregando.set(true);
    this.service.perfil(this.clienteId).subscribe({
      next: (p) => { this.perfil.set(p); this.carregando.set(false); },
      error: () => { this.carregando.set(false); this.snack.open('Erro ao carregar o cliente.', 'OK', { duration: 4000 }); },
    });
  }

  voltar(): void { this.router.navigate(['/clientes']); }
  alternarForm(): void { this.mostrarForm.update((v) => !v); }

  salvarVenda(): void {
    if (!this.nova.valor_total || this.nova.valor_total < 1) {
      this.snack.open('Informe um valor de pelo menos R$ 1,00.', 'OK', { duration: 3000 }); return;
    }
    if (!this.nova.num_parcelas || this.nova.num_parcelas < 1 || this.nova.num_parcelas > 60) {
      this.snack.open('Número de parcelas deve ser entre 1 e 60.', 'OK', { duration: 3000 }); return;
    }
    if (!this.nova.data_primeira_parcela) {
      this.snack.open('Informe a data da 1ª parcela.', 'OK', { duration: 3000 }); return;
    }
    this.salvando.set(true);
    this.service.registrarVenda({
      cliente_id: this.clienteId,
      valor_total: this.nova.valor_total,
      num_parcelas: this.nova.num_parcelas,
      data_primeira_parcela: this.nova.data_primeira_parcela,
    }).subscribe({
      next: () => {
        this.snack.open('Venda registrada!', 'OK', { duration: 3000 });
        this.nova = { valor_total: null, num_parcelas: 1, data_primeira_parcela: '' };
        this.mostrarForm.set(false); this.salvando.set(false);
        this.carregar();
      },
      error: () => { this.salvando.set(false); this.snack.open('Erro ao registrar a venda.', 'OK', { duration: 4000 }); },
    });
  }

  pagar(parcelaId: string): void {
    this.service.pagarParcela(parcelaId).subscribe({
      next: () => { this.snack.open('Pagamento confirmado!', 'OK', { duration: 3000 }); this.carregar(); },
      error: () => this.snack.open('Erro ao confirmar pagamento.', 'OK', { duration: 4000 }),
    });
  }

  cancelar(vendaId: string): void {
    this.service.cancelarVenda(vendaId).subscribe({
      next: () => { this.snack.open('Venda cancelada.', 'OK', { duration: 3000 }); this.carregar(); },
      error: () => this.snack.open('Erro ao cancelar a venda.', 'OK', { duration: 4000 }),
    });
  }

  dinheiro(v: number): string { return 'R$ ' + v.toFixed(2).replace('.', ','); }
  data(iso: string): string { const [a, m, d] = iso.split('-'); return `${d}/${m}/${a}`; }
  rotuloStatus(s: string): string {
    return { pendente: 'Pendente', atrasada: 'Atrasada', aguardando_confirmacao: 'Aguardando', paga: 'Paga' }[s] ?? s;
  }
}
