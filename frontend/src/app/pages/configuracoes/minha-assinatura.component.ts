import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AssinaturaService, MinhaAssinatura } from '../../core/assinatura.service';
import { dataHoraLocal } from '../../core/datas';

const ROTULOS: Record<string, string> = {
  em_teste: 'Período de teste',
  ativa: 'Assinatura ativa',
  vencida: 'Assinatura vencida',
  isenta: 'Administração',
};

@Component({
  selector: 'app-minha-assinatura',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatProgressSpinnerModule,
  ],
  template: `
    <mat-card class="bloco assinatura" id="assinatura">
      <div class="topo">
        <h3>Minha assinatura</h3>
        @if (dados(); as a) {
          <span class="selo {{ a.situacao }}">{{ rotulo(a.situacao) }}</span>
        }
      </div>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="32"></mat-spinner></div>
      } @else {
        @if (dados(); as a) {
          @if (a.situacao === 'isenta') {
            <!-- Administração: sem validade, sem cobrança. Mostrar uma data aqui
                 seria mentir, porque a trava nunca bloqueia esta conta. -->
            <p class="aviso-isenta">
              <mat-icon inline>verified_user</mat-icon>
              <span>
                Conta de administração: sem cobrança e sem bloqueio. Você usa o sistema
                inteiro e confere os comprovantes em <strong>Comprovantes</strong>.
              </span>
            </p>
          } @else {
          <div class="resumo">
            <div class="coluna">
              <span class="rotulo">
                @if (a.situacao === 'vencida') { Venceu em } @else { Válida até }
              </span>
              <span class="valor">{{ a.valido_ate ? data(a.valido_ate) : '—' }}</span>
              @if (a.situacao !== 'vencida' && a.dias_restantes > 0) {
                <span class="descricao">
                  {{ a.dias_restantes }} {{ a.dias_restantes === 1 ? 'dia' : 'dias' }} restantes
                </span>
              }
            </div>
            <div class="coluna">
              <span class="rotulo">Mensalidade</span>
              <span class="valor">{{ dinheiro(a.valor_mensal) }}</span>
              <span class="descricao">a cada 30 dias</span>
            </div>
          </div>

          @if (a.situacao === 'vencida') {
            <p class="alerta">
              <mat-icon inline>lock</mat-icon>
              Você continua vendo tudo, mas não consegue cadastrar, cobrar nem conectar o
              WhatsApp até renovar.
            </p>
          }

          <!-- Pagamento ------------------------------------------------------>
          @if (a.tem_pendente) {
            <div class="pendente">
              <mat-icon inline>schedule</mat-icon>
              Seu comprovante está em análise. Assim que for conferido, o acesso é liberado.
            </div>
          } @else {
            <div class="pagar">
              <span class="rotulo">1. Pague por Pix</span>
              @if (a.pix_chave) {
                <div class="chave">
                  <code>{{ a.pix_chave }}</code>
                  <button mat-button (click)="copiar(a.pix_chave)">
                    <mat-icon>content_copy</mat-icon> Copiar
                  </button>
                </div>
                @if (a.pix_nome) { <span class="descricao">Em nome de {{ a.pix_nome }}</span> }
              } @else {
                <span class="descricao">A chave Pix ainda não foi configurada.</span>
              }

              <span class="rotulo segundo">2. Envie o comprovante</span>
              <div class="envio">
                <mat-form-field appearance="outline" class="campo-valor">
                  <mat-label>Valor pago (R$)</mat-label>
                  <input matInput type="number" step="0.01" min="0.01" [(ngModel)]="valor"
                         name="valor" />
                </mat-form-field>

                <button mat-stroked-button type="button" (click)="seletor.click()">
                  <mat-icon>attach_file</mat-icon>
                  {{ arquivo() ? arquivo()!.name : 'Escolher arquivo' }}
                </button>
                <input #seletor type="file" hidden accept="image/jpeg,image/png,application/pdf"
                       (change)="escolher($event)" />

                <button mat-raised-button color="primary" [disabled]="enviando()"
                        (click)="enviar()">
                  <mat-icon>send</mat-icon> Enviar
                </button>
              </div>
              <span class="descricao">Imagem ou PDF, até 5 MB.</span>
            </div>
          }

          }

          <!-- Histórico ------------------------------------------------------>
          @if (a.historico.length > 0) {
            <div class="historico">
              <span class="rotulo">Envios anteriores</span>
              @for (p of a.historico; track p.id) {
                <div class="item">
                  <span class="quando">{{ dataHora(p.enviado_em) }}</span>
                  <span class="quanto">{{ dinheiro(p.valor) }}</span>
                  <span class="chip {{ p.situacao }}">{{ rotuloPagamento(p.situacao) }}</span>
                  @if (p.observacao) { <span class="motivo">{{ p.observacao }}</span> }
                </div>
              }
            </div>
          }
        }
      }
    </mat-card>
  `,
  styles: [`
    .bloco { padding: 16px; margin-bottom: 16px; }
    .topo { display: flex; align-items: center; justify-content: space-between; gap: 12px;
            flex-wrap: wrap; margin-bottom: 14px; }
    /* Mesmo verde dos demais títulos de bloco das Configurações. */
    .topo h3 { margin: 0; color: var(--verde-800); }
    .centro { display: flex; justify-content: center; padding: 24px; }

    /* A etiqueta de situação é o dado mais consultado deste cartão: ganha
       contorno próprio em vez de ser só um fundo pastel. */
    .selo {
      font-size: 0.75rem; font-weight: 600; padding: 5px 13px; border-radius: 999px;
      border: 1px solid transparent;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
    }
    .selo.ativa    { background: var(--sucesso-bg); color: var(--sucesso);
                     border-color: rgba(31, 130, 77, 0.22); }
    .selo.em_teste { background: var(--info-bg); color: var(--info);
                     border-color: rgba(41, 148, 91, 0.22); }
    .selo.vencida  { background: var(--perigo-bg); color: var(--perigo);
                     border-color: rgba(192, 57, 43, 0.22); }
    .selo.isenta   { background: var(--petroleo-800); color: var(--lima-400);
                     border-color: rgba(168, 227, 74, 0.35); }

    /* Nome próprio: "isenta" já é a variação da etiqueta (.selo.isenta), e
       reaproveitar a classe fazia uma herdar o estilo da outra. O texto vai num
       span único porque o contêiner é flexível: solto, cada trecho em negrito
       virava um item separado. */
    .aviso-isenta {
      display: flex; align-items: flex-start; gap: 8px; margin: 0;
      padding: 11px 13px; border-radius: var(--raio-interno);
      background: var(--verde-50); color: var(--texto);
      border: 1px solid rgba(31, 130, 77, 0.18);
      font-size: 0.9rem; line-height: 1.5;
    }
    .aviso-isenta mat-icon { color: var(--verde-800); flex-shrink: 0; margin-top: 2px; }

    .resumo { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
              gap: 12px; margin-bottom: 14px; }
    .coluna { display: flex; flex-direction: column; }
    .rotulo { font-size: 0.8rem; color: var(--texto-suave); font-weight: 600; }
    .valor { font-size: 1.3rem; font-weight: 600; margin-top: 2px; }
    .descricao { font-size: 0.8rem; color: var(--texto-suave); }

    .alerta, .pendente {
      display: flex; align-items: flex-start; gap: 8px;
      padding: 11px 13px; border-radius: var(--raio-interno);
      font-size: 0.9rem; line-height: 1.5;
      border: 1px solid transparent;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
    }
    .alerta { margin: 0 0 14px; background: var(--perigo-bg); color: var(--perigo);
              border-color: rgba(192, 57, 43, 0.18); }
    .pendente { align-items: center; background: var(--alerta-bg); color: var(--alerta);
                border-color: rgba(178, 106, 0, 0.20); }

    .pagar { display: flex; flex-direction: column; gap: 6px; }
    .rotulo.segundo { margin-top: 14px; }
    /* A chave Pix é para copiar: o miolo afunda, como um campo, para dizer
       "isto é conteúdo", não "isto é um botão". */
    .chave {
      display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
      background-image: linear-gradient(180deg, #eef8f2 0%, #e6f4ec 100%);
      border: 1px solid rgba(31, 130, 77, 0.18);
      border-radius: var(--raio-interno);
      box-shadow: inset 0 1px 3px rgba(15, 98, 52, 0.10);
      padding: 6px 6px 6px 12px;
    }
    .chave code { font-size: 0.95rem; word-break: break-all; }
    .envio { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 4px; }
    .campo-valor { width: 160px; }

    .historico { margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--borda); }
    .item { display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
            padding: 8px 0; border-bottom: 1px solid var(--borda); font-size: 0.9rem; }
    .item:last-child { border-bottom: none; }
    .quando { color: var(--texto-suave); }
    .quanto { font-weight: 600; }
    .motivo { color: var(--texto-suave); font-style: italic; }
    .chip { padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 500; }
    .chip.aprovado { background: var(--sucesso-bg); color: var(--sucesso); }
    .chip.pendente { background: var(--alerta-bg); color: var(--alerta); }
    .chip.recusado { background: var(--perigo-bg); color: var(--perigo); }
  `],
})
export class MinhaAssinaturaComponent implements OnInit {
  private service = inject(AssinaturaService);
  private aviso = inject(MatSnackBar);

  readonly dados = signal<MinhaAssinatura | null>(null);
  readonly carregando = signal<boolean>(true);
  readonly enviando = signal<boolean>(false);
  readonly arquivo = signal<File | null>(null);
  valor: number | null = null;

  ngOnInit(): void {
    this.carregar();
  }

  private carregar(): void {
    this.carregando.set(true);
    this.service.carregar().subscribe({
      next: (a) => {
        this.dados.set(a);
        if (this.valor === null) this.valor = a.valor_mensal;
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }

  escolher(evento: Event): void {
    const alvo = evento.target as HTMLInputElement;
    this.arquivo.set(alvo.files?.[0] ?? null);
  }

  copiar(chave: string): void {
    navigator.clipboard?.writeText(chave).then(
      () => this.aviso.open('Chave Pix copiada', 'OK', { duration: 2500 }),
      () => this.aviso.open('Não foi possível copiar. Selecione e copie à mão.', 'OK',
                            { duration: 4000 }),
    );
  }

  enviar(): void {
    const arq = this.arquivo();
    if (!this.valor || this.valor <= 0) {
      this.aviso.open('Informe o valor que você pagou.', 'OK', { duration: 3000 });
      return;
    }
    if (!arq) {
      this.aviso.open('Escolha o arquivo do comprovante.', 'OK', { duration: 3000 });
      return;
    }
    this.enviando.set(true);
    this.service.enviarComprovante(this.valor, arq).subscribe({
      next: () => {
        this.enviando.set(false);
        this.arquivo.set(null);
        this.aviso.open('Comprovante enviado. Você recebe o acesso assim que for conferido.',
                        'OK', { duration: 5000 });
        this.carregar();
      },
      error: (erro) => {
        this.enviando.set(false);
        const msg = erro.status === 409
          ? 'Você já tem um comprovante em análise.'
          : erro.error?.detail ?? 'Não foi possível enviar o comprovante.';
        this.aviso.open(msg, 'OK', { duration: 5000 });
      },
    });
  }

  rotulo(s: string): string { return ROTULOS[s] ?? s; }
  rotuloPagamento(s: string): string {
    return { pendente: 'Em análise', aprovado: 'Aprovado', recusado: 'Recusado' }[s] ?? s;
  }
  dinheiro(v: number): string { return 'R$ ' + v.toFixed(2).replace('.', ','); }
  data(iso: string): string { const [a, m, d] = iso.split('-'); return `${d}/${m}/${a}`; }
  dataHora(iso: string): string { return dataHoraLocal(iso); }
}
