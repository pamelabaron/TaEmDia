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
import { bloqueadoPorAssinatura } from '../../core/erros';
import {
  CODIGO_PAIS_PADRAO, conferirCpf, conferirTelefone, formatarTelefone,
} from '../../core/regras-cliente';

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
              <input matInput [(ngModel)]="novo.nome" name="nome" maxlength="120" />
            </mat-form-field>
            <div class="linha-telefone">
              <mat-form-field appearance="outline" class="campo-pais">
                <mat-label>País</mat-label>
                <span matTextPrefix>+&nbsp;</span>
                <input matInput [(ngModel)]="novo.codigo_pais" name="codigoPais"
                       inputmode="numeric" maxlength="3" />
              </mat-form-field>
              <mat-form-field appearance="outline" class="campo-numero">
                <mat-label>WhatsApp com DDD</mat-label>
                <input matInput [(ngModel)]="novo.whatsapp_numero" name="whatsapp"
                       inputmode="tel" maxlength="16" placeholder="(47) 99999-0000" />
                @if (erroTelefone(); as erro) {
                  <mat-error>{{ erro }}</mat-error>
                } @else {
                  <mat-hint>{{ previaDoTelefone() }}</mat-hint>
                }
              </mat-form-field>
            </div>
            <mat-form-field appearance="outline" class="campo">
              <mat-label>CPF (opcional)</mat-label>
              <input matInput [(ngModel)]="novo.cpf" name="cpf"
                     inputmode="numeric" maxlength="14" placeholder="000.000.000-00" />
              @if (erroCpf(); as erro) {
                <mat-error>{{ erro }}</mat-error>
              }
            </mat-form-field>
            <mat-form-field appearance="outline" class="campo">
              <mat-label>Endereço (opcional)</mat-label>
              <input matInput [(ngModel)]="novo.endereco" name="endereco" maxlength="200" />
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
        <input matInput [(ngModel)]="termo" name="busca" maxlength="60" />
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
                <div matListItemLine>{{ c.whatsapp_formatado }}</div>
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
    /* O código do país fica estreito e sempre na frente do número: é o que
       a pessoa quase nunca muda, mas precisa enxergar. */
    .linha-telefone { display: flex; gap: 10px; align-items: flex-start; }
    .campo-pais { width: 96px; flex: 0 0 96px; }
    .campo-numero { flex: 1; min-width: 0; }
    .busca { margin-bottom: 8px; }
    .centro { display: flex; justify-content: center; padding: 32px; }
    .vazio { text-align: center; color: var(--texto-fraco); padding: 24px; }
    .clicavel { cursor: pointer; }

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
  novo = {
    nome: '',
    codigo_pais: CODIGO_PAIS_PADRAO,
    whatsapp_numero: '',
    cpf: '',
    endereco: '',
  };

  // Lista filtrada em tempo real por nome ou WhatsApp.
  readonly filtrados = computed(() => {
    const t = this.termo.trim().toLowerCase();
    if (!t) return this.clientes();
    return this.clientes().filter(
      (c) =>
        c.nome.toLowerCase().includes(t)
        || c.whatsapp_numero.includes(t)
        || c.whatsapp_formatado.includes(t),
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

  /** O erro do telefone, ou vazio. Só fala depois que a pessoa digitou algo:
   *  reclamar de campo em branco enquanto ela ainda escreve é ruído. */
  erroTelefone(): string {
    if (!this.novo.whatsapp_numero.trim()) return '';
    const r = conferirTelefone(this.novo.whatsapp_numero, this.novo.codigo_pais);
    return r.ok ? '' : r.erro;
  }

  /** Mostra como o número vai ficar guardado, enquanto a pessoa digita. */
  previaDoTelefone(): string {
    if (!this.novo.whatsapp_numero.trim()) return 'Exemplo: 47 99999-0000';
    const r = conferirTelefone(this.novo.whatsapp_numero, this.novo.codigo_pais);
    return r.ok ? `Será salvo como ${formatarTelefone(r.valor)}` : '';
  }

  erroCpf(): string {
    if (!this.novo.cpf.trim()) return '';
    const r = conferirCpf(this.novo.cpf);
    return r.ok ? '' : r.erro;
  }

  salvar(): void {
    if (!this.novo.nome.trim()) {
      this.snack.open('Preencha o nome.', 'OK', { duration: 3000 });
      return;
    }

    // A API confere de novo. Aqui é só para a pessoa não esperar a viagem
    // até o servidor para descobrir que faltou um dígito.
    const telefone = conferirTelefone(this.novo.whatsapp_numero, this.novo.codigo_pais);
    if (!telefone.ok) {
      this.snack.open(telefone.erro, 'OK', { duration: 4000 });
      return;
    }
    const cpf = conferirCpf(this.novo.cpf);
    if (!cpf.ok) {
      this.snack.open(cpf.erro, 'OK', { duration: 4000 });
      return;
    }

    this.salvando.set(true);
    this.service.criar({
      nome: this.novo.nome.trim(),
      codigo_pais: this.novo.codigo_pais.trim() || CODIGO_PAIS_PADRAO,
      whatsapp_numero: telefone.valor,
      cpf: cpf.valor || null,
      endereco: this.novo.endereco.trim() || null,
    }).subscribe({
      next: () => {
        this.snack.open('Cliente cadastrado', 'OK', { duration: 3000 });
        this.novo = {
          nome: '', codigo_pais: CODIGO_PAIS_PADRAO,
          whatsapp_numero: '', cpf: '', endereco: '',
        };
        this.mostrarForm.set(false);
        this.salvando.set(false);
        this.carregar();
      },
      error: (erro) => {
        this.salvando.set(false);
        if (bloqueadoPorAssinatura(erro)) return;
        const msg = erro.status === 409
          ? 'Já existe um cliente com esse número de WhatsApp.'
          : 'Erro ao cadastrar cliente.';
        this.snack.open(msg, 'OK', { duration: 4000 });
      },
    });
  }
}
