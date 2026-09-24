import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatSnackBar } from '@angular/material/snack-bar';
import {
  AssinaturaService,
  ComprovanteAdmin,
  SituacaoComprovante,
} from '../../core/assinatura.service';
import { dataHoraLocal } from '../../core/datas';

interface Aba { situacao: SituacaoComprovante; titulo: string; }

const ABAS: Aba[] = [
  { situacao: 'pendente', titulo: 'Aguardando' },
  { situacao: 'aprovado', titulo: 'Aprovados' },
  { situacao: 'recusado', titulo: 'Recusados' },
];

/** Texto do estado vazio de cada aba: fila vazia é boa notícia, histórico vazio não. */
const VAZIO: Record<SituacaoComprovante, { icone: string; titulo: string; texto: string }> = {
  pendente: {
    icone: 'inbox',
    titulo: 'Nenhum comprovante aguardando',
    texto: 'Quando alguém enviar um Pix, ele aparece aqui para conferência.',
  },
  aprovado: {
    icone: 'task_alt',
    titulo: 'Nenhum comprovante aprovado ainda',
    texto: 'Os comprovantes que você aprovar ficam registrados aqui.',
  },
  recusado: {
    icone: 'block',
    titulo: 'Nenhum comprovante recusado',
    texto: 'Os comprovantes que você recusar ficam aqui, com o motivo.',
  },
};

/**
 * Conferência de comprovantes. Visível apenas para quem está em ADMIN_EMAILS.
 *
 * Esconder a tela é conforto: quem não é administrador recebe 403 do servidor
 * mesmo chamando os endpoints direto.
 */
@Component({
  selector: 'app-assinaturas',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatButtonModule, MatIconModule, MatTabsModule,
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

      @if (semAcesso()) {
        <mat-card class="bloco vazio-card">
          <mat-icon class="icone-grande">lock</mat-icon>
          <h3>Área restrita</h3>
          <p>Esta tela é da administração do sistema.</p>
        </mat-card>
      } @else {
        <mat-tab-group class="abas" mat-stretch-tabs="true" [selectedIndex]="indiceAba()"
                       (selectedIndexChange)="trocarAba($event)" animationDuration="0ms">
          @for (a of abas; track a.situacao) {
            <mat-tab>
              <ng-template mat-tab-label>
                {{ a.titulo }}
                @if (a.situacao === 'pendente' && quantidadeAguardando() > 0) {
                  <span class="contador">{{ quantidadeAguardando() }}</span>
                }
              </ng-template>
            </mat-tab>
          }
        </mat-tab-group>

        @if (carregando()) {
          <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
        } @else if (itens().length === 0) {
          <mat-card class="bloco vazio-card">
            <mat-icon class="icone-grande">{{ vazio().icone }}</mat-icon>
            <h3>{{ vazio().titulo }}</h3>
            <p>{{ vazio().texto }}</p>
          </mat-card>
        } @else {
          @for (p of itens(); track p.id) {
            <mat-card class="bloco item" [class.historico]="aba() !== 'pendente'">
              <div class="quem">
                <div>
                  <strong>{{ p.vendedor_nome || 'Sem nome' }}</strong>
                  <span class="email">{{ p.vendedor_email }}</span>
                </div>
                <div class="valor">{{ dinheiro(p.valor) }}</div>
              </div>

              <div class="meta">
                <span class="datas">
                  <mat-icon inline>schedule</mat-icon>
                  Enviado {{ dataHora(p.enviado_em) }}
                  @if (p.avaliado_em) {
                    <span class="separador">·</span>
                    <span class="avaliacao {{ p.situacao }}">
                      {{ p.situacao === 'aprovado' ? 'Aprovado' : 'Recusado' }}
                      {{ dataHora(p.avaliado_em) }}
                    </span>
                  }
                </span>
                <button mat-button (click)="abrir(p)">
                  <mat-icon>visibility</mat-icon> Ver comprovante
                </button>
              </div>

              @if (p.situacao === 'recusado' && p.observacao) {
                <p class="motivo"><strong>Motivo:</strong> {{ p.observacao }}</p>
              }

              <!-- Ações só na fila: o histórico é consulta. -->
              @if (p.situacao === 'pendente') {
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
              }
            </mat-card>
          }
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

    .abas { margin-bottom: 16px; }
    /* No celular as três abas precisam caber lado a lado: o Material esconde
       as que sobram atrás de uma seta, e aba escondida é aba que ninguém acha.
       O espaçamento interno padrão (24px de cada lado) é o que não cabia. */
    @media (max-width: 480px) {
      :host ::ng-deep .abas .mat-mdc-tab {
        min-width: 0; padding-left: 8px; padding-right: 8px;
      }
      :host ::ng-deep .abas .mdc-tab__text-label { letter-spacing: 0; }
    }
    /* O número na aba "Aguardando" diz de longe se há trabalho a fazer. */
    .contador {
      display: inline-flex; align-items: center; justify-content: center;
      min-width: 20px; height: 20px; padding: 0 6px; margin-left: 8px;
      border-radius: 999px; font-size: 0.75rem; font-weight: 700;
      background: var(--verde-800); color: #fff;
      font-variant-numeric: tabular-nums;
    }

    /* Fila vazia é o estado normal, não uma falha: recebe respiro e uma luz
       suave em vez de parecer erro. */
    .vazio-card {
      text-align: center; padding: 52px 24px 48px; overflow: hidden;
    }
    .vazio-card::before {
      content: ""; position: absolute; inset: 0; pointer-events: none;
      background: radial-gradient(24rem 12rem at 50% 0%, rgba(60, 182, 118, 0.10), transparent 70%);
    }
    .vazio-card > * { position: relative; }
    .vazio-card h3 { margin: 12px 0 4px; }
    .vazio-card p { color: var(--texto-suave); margin: 0; }
    .icone-grande { font-size: 40px; width: 40px; height: 40px; color: var(--texto-fraco); }

    .quem { display: flex; align-items: flex-start; justify-content: space-between;
            gap: 12px; flex-wrap: wrap; }
    .quem > div:first-child { display: flex; flex-direction: column; }
    .email { font-size: 0.85rem; color: var(--texto-suave); }
    .valor { font-size: 1.35rem; font-weight: 600; color: var(--verde-800);
             letter-spacing: -0.02em; font-variant-numeric: tabular-nums; }

    .meta { display: flex; align-items: center; justify-content: space-between;
            gap: 12px; flex-wrap: wrap; margin-top: 8px;
            font-size: 0.85rem; color: var(--texto-suave); }
    .datas { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
    .separador { color: var(--texto-fraco); }
    /* A situação da avaliação usa as cores de significado do projeto. */
    .avaliacao { font-weight: 600; }
    .avaliacao.aprovado { color: var(--sucesso); }
    .avaliacao.recusado { color: var(--perigo); }

    .motivo {
      margin: 10px 0 0; padding: 9px 12px; border-radius: var(--raio-interno);
      background: var(--perigo-bg); color: var(--texto); font-size: 0.9rem; line-height: 1.5;
      border: 1px solid rgba(192, 57, 43, 0.18);
    }
    .motivo strong { color: var(--perigo); }

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

  readonly abas = ABAS;
  readonly aba = signal<SituacaoComprovante>('pendente');
  readonly itens = signal<ComprovanteAdmin[]>([]);
  readonly quantidadeAguardando = signal<number>(0);
  readonly carregando = signal<boolean>(true);
  readonly agindo = signal<boolean>(false);
  readonly semAcesso = signal<boolean>(false);
  readonly recusando = signal<string | null>(null);
  motivo = '';

  ngOnInit(): void {
    this.carregar();
  }

  indiceAba(): number { return ABAS.findIndex((a) => a.situacao === this.aba()); }
  vazio() { return VAZIO[this.aba()]; }

  trocarAba(indice: number): void {
    this.aba.set(ABAS[indice].situacao);
    this.recusando.set(null);
    this.carregar();
  }

  /** Carrega a aba atual. A contagem da fila é atualizada em qualquer aba. */
  carregar(): void {
    this.carregando.set(true);
    const situacao = this.aba();
    this.service.listar(situacao).subscribe({
      next: (lista) => {
        // Descarta a resposta de uma aba que a pessoa já deixou.
        if (situacao !== this.aba()) return;
        this.itens.set(lista);
        this.semAcesso.set(false);
        this.carregando.set(false);
        if (situacao === 'pendente') this.quantidadeAguardando.set(lista.length);
      },
      error: (erro) => {
        this.semAcesso.set(erro.status === 403);
        this.carregando.set(false);
      },
    });
    if (situacao !== 'pendente') {
      this.service.listar('pendente').subscribe({
        next: (fila) => this.quantidadeAguardando.set(fila.length),
        error: () => undefined,
      });
    }
  }

  /** Abre o arquivo numa aba nova. Vem por endpoint autenticado, não por URL pública. */
  abrir(p: ComprovanteAdmin): void {
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

  aprovar(p: ComprovanteAdmin): void {
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

  pedirMotivo(p: ComprovanteAdmin): void {
    this.motivo = '';
    this.recusando.set(p.id);
  }

  confirmarRecusa(p: ComprovanteAdmin): void {
    if (this.motivo.trim().length < 3) {
      this.aviso.open('Escreva o motivo. A pessoa vai ler.', 'OK', { duration: 3000 });
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
  dataHora(iso: string): string { return dataHoraLocal(iso); }
}
