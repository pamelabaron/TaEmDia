import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Cliente, ClientesService } from '../../core/clientes.service';

@Component({
  selector: 'app-clientes',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatListModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="pagina">
      <div class="cabecalho">
        <h2>Clientes</h2>
        <button mat-raised-button color="primary" (click)="alternarFormulario()">
          <mat-icon>{{ mostrarForm() ? 'close' : 'add' }}</mat-icon>
          {{ mostrarForm() ? 'Cancelar' : 'Novo cliente' }}
        </button>
      </div>

      @if (mostrarForm()) {
        <mat-card class="form-card">
          <mat-card-content>
            <mat-form-field appearance="outline" class="campo">
              <mat-label>Nome completo</mat-label>
              <input matInput [(ngModel)]="novo.nome" name="nome" />
            </mat-form-field>
            <mat-form-field appearance="outline" class="campo">
              <mat-label>WhatsApp (só números, com DDD)</mat-label>
              <input matInput [(ngModel)]="novo.whatsapp_numero" name="whatsapp" placeholder="5547999990000" />
            </mat-form-field>
            <mat-form-field appearance="outline" class="campo">
              <mat-label>CPF (opcional)</mat-label>
              <input matInput [(ngModel)]="novo.cpf" name="cpf" />
            </mat-form-field>
            <mat-form-field appearance="outline" class="campo">
              <mat-label>Endereço (opcional)</mat-label>
              <input matInput [(ngModel)]="novo.endereco" name="endereco" />
            </mat-form-field>
            <button mat-raised-button color="primary" [disabled]="salvando()" (click)="salvar()">
              Salvar cliente
            </button>
          </mat-card-content>
        </mat-card>
      }

      <mat-form-field appearance="outline" class="busca">
        <mat-icon matPrefix>search</mat-icon>
        <mat-label>Buscar por nome ou WhatsApp</mat-label>
        <input matInput [(ngModel)]="termo" name="busca" />
      </mat-form-field>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else if (filtrados().length === 0) {
        <p class="vazio">Nenhum cliente encontrado.</p>
      } @else {
        <mat-card>
          <mat-list>
            @for (c of filtrados(); track c.id) {
              <mat-list-item class="clicavel" (click)="abrirPerfil(c.id)">
                <mat-icon matListItemIcon>person</mat-icon>
                <div matListItemTitle>{{ c.nome }}</div>
                <div matListItemLine>{{ c.whatsapp_numero }}</div>
                <mat-icon matListItemMeta>chevron_right</mat-icon>
              </mat-list-item>
            }
          </mat-list>
        </mat-card>
      }
    </div>
  `,
  styles: [`
    .pagina { max-width: 720px; margin: 0 auto; padding: 16px; }
    .cabecalho { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
    .cabecalho h2 { margin: 0; }
    .form-card { margin-bottom: 16px; }
    .campo, .busca { width: 100%; }
    .busca { margin-bottom: 8px; }
    .centro { display: flex; justify-content: center; padding: 32px; }
    .vazio { text-align: center; color: #888; padding: 24px; }
    .clicavel { cursor: pointer; }
    .clicavel:hover { background: #f5f5f5; }
  `],
})
export class ClientesComponent implements OnInit {
  private service = inject(ClientesService);
  private snack = inject(MatSnackBar);
  private router = inject(Router);

  readonly clientes = signal<Cliente[]>([]);
  readonly carregando = signal<boolean>(true);
  readonly salvando = signal<boolean>(false);
  readonly mostrarForm = signal<boolean>(false);
  termo = '';
  novo = { nome: '', whatsapp_numero: '', cpf: '', endereco: '' };

  // Lista filtrada em tempo real por nome ou WhatsApp.
  readonly filtrados = computed(() => {
    const t = this.termo.trim().toLowerCase();
    if (!t) return this.clientes();
    return this.clientes().filter(
      (c) => c.nome.toLowerCase().includes(t) || c.whatsapp_numero.includes(t),
    );
  });

  ngOnInit(): void {
    this.carregar();
  }

  private carregar(): void {
    this.carregando.set(true);
    this.service.listar().subscribe({
      next: (lista) => { this.clientes.set(lista); this.carregando.set(false); },
      error: () => { this.carregando.set(false); this.snack.open('Erro ao carregar clientes.', 'OK', { duration: 4000 }); },
    });
  }

  alternarFormulario(): void {
    this.mostrarForm.update((v) => !v);
  }

  abrirPerfil(clienteId: string): void {
    this.router.navigate(['/clientes', clienteId]);
  }

  salvar(): void {
    if (!this.novo.nome.trim() || !this.novo.whatsapp_numero.trim()) {
      this.snack.open('Preencha nome e WhatsApp.', 'OK', { duration: 3000 });
      return;
    }
    this.salvando.set(true);
    this.service.criar({
      nome: this.novo.nome.trim(),
      whatsapp_numero: this.novo.whatsapp_numero.trim(),
      cpf: this.novo.cpf.trim() || null,
      endereco: this.novo.endereco.trim() || null,
    }).subscribe({
      next: () => {
        this.snack.open('Cliente cadastrado!', 'OK', { duration: 3000 });
        this.novo = { nome: '', whatsapp_numero: '', cpf: '', endereco: '' };
        this.mostrarForm.set(false);
        this.salvando.set(false);
        this.carregar();
      },
      error: (erro) => {
        this.salvando.set(false);
        const msg = erro.status === 409
          ? 'Já existe um cliente com esse número de WhatsApp.'
          : 'Erro ao cadastrar cliente.';
        this.snack.open(msg, 'OK', { duration: 4000 });
      },
    });
  }
}
