import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import {
  CanalResumo,
  Configuracao,
  ConfiguracoesService,
  ResumoDoDia,
} from '../../core/configuracoes.service';
import { bloqueadoPorAssinatura } from '../../core/erros';

// Horários possíveis para o resumo (fim do dia, conforme o RFC).
const HORARIOS = ['18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00'];

/** O resumo do dia: como receber, e o que aconteceu nos últimos dias. */
@Component({
  selector: 'app-config-resumo',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatButtonModule, MatButtonToggleModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule, MatSlideToggleModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="pagina-config">
      <h2>Resumo diário</h2>
      <p class="ajuda">Um retrato do dia: cobranças enviadas, pagamentos e respostas.</p>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        @if (config; as c) {
          <!-- ================================================= como receber -->
          <mat-card class="bloco">
            <h3>Como você recebe</h3>

            <div class="linha">
              <div class="texto">
                <span class="rotulo">Receber resumo diário</span>
                <span class="descricao">
                  Desligue se preferir consultar o sistema por conta própria.
                </span>
              </div>
              <mat-slide-toggle [(ngModel)]="c.resumo_ativo" name="resumoAtivo">
              </mat-slide-toggle>
            </div>

            <div class="linha">
              <div class="texto">
                <span class="rotulo">Horário do resumo</span>
                <span class="descricao">A que horas você quer receber.</span>
              </div>
              <mat-form-field appearance="outline" class="campo-curto">
                <mat-label>Horário</mat-label>
                <mat-select [(ngModel)]="horario" name="horario" [disabled]="!c.resumo_ativo">
                  @for (h of horarios; track h) {
                    <mat-option [value]="h">{{ h }}</mat-option>
                  }
                </mat-select>
              </mat-form-field>
            </div>

            <div class="linha">
              <div class="texto">
                <span class="rotulo">Por onde</span>
                <span class="descricao">Escolha um canal, ou os dois.</span>
              </div>
              <mat-button-toggle-group [(ngModel)]="c.canal_resumo" name="canal"
                                       [disabled]="!c.resumo_ativo" aria-label="Canal do resumo">
                <mat-button-toggle value="whatsapp">WhatsApp</mat-button-toggle>
                <mat-button-toggle value="email">E-mail</mat-button-toggle>
                <mat-button-toggle value="ambos">Ambos</mat-button-toggle>
              </mat-button-toggle-group>
            </div>

            @if (querWhatsapp()) {
              <div class="linha">
                <div class="texto">
                  <span class="rotulo">WhatsApp que recebe</span>
                  <span class="descricao">
                    Deixe em branco para usar o mesmo número que faz as cobranças.
                  </span>
                </div>
                <mat-form-field appearance="outline" class="campo-email">
                  <mat-label>Número com DDD</mat-label>
                  <input matInput [(ngModel)]="c.whatsapp_resumo" name="whatsappResumo"
                         inputmode="tel" maxlength="20"
                         placeholder="47999990000" />
                </mat-form-field>
              </div>
            }

            @if (querEmail()) {
              <div class="linha">
                <div class="texto">
                  <span class="rotulo">E-mail que recebe</span>
                  <span class="descricao">Para onde o resumo deve ser enviado.</span>
                </div>
                <mat-form-field appearance="outline" class="campo-email">
                  <mat-label>E-mail</mat-label>
                  <input matInput type="email" [(ngModel)]="c.email_resumo" name="emailResumo"
                         maxlength="120"
                         placeholder="voce@exemplo.com" />
                </mat-form-field>
              </div>

              <p class="nota">
                <mat-icon inline>info</mat-icon>
                O envio por e-mail ainda não está ligado: falta cadastrar um serviço de
                envio. A escolha fica guardada e passa a valer assim que isso for feito.
              </p>
            }
          </mat-card>

          <div class="acoes">
            <button mat-button [disabled]="salvando() || !mudou()" (click)="cancelar()">
              Cancelar
            </button>
            <button mat-raised-button color="primary" [disabled]="salvando() || !mudou()"
                    (click)="salvar()">
              <mat-icon>save</mat-icon> Salvar
            </button>
          </div>
        }

        <!-- ================================================ o que aconteceu -->
        <mat-card class="bloco">
          <div class="cabecalho-resumo">
            <h3>O que aconteceu</h3>
            <div class="ferramentas">
              <mat-form-field appearance="outline" class="campo-dia">
                <mat-label>Dia</mat-label>
                <mat-select [(ngModel)]="diaEscolhido" name="dia"
                            (ngModelChange)="carregarResumo()">
                  @for (d of dias(); track d) {
                    <mat-option [value]="d">{{ rotuloDia(d) }}</mat-option>
                  }
                </mat-select>
              </mat-form-field>
              <button mat-stroked-button (click)="exportar()" [disabled]="exportando()">
                <mat-icon>picture_as_pdf</mat-icon> Exportar PDF
              </button>
            </div>
          </div>
          <p class="descricao janela">O resumo guarda os últimos 7 dias.</p>

          @if (carregandoResumo()) {
            <div class="centro"><mat-spinner diameter="32"></mat-spinner></div>
          } @else {
            @if (resumo(); as r) {
            @if (!r.houve_atividade) {
              <p class="vazio">Nenhuma atividade neste dia.</p>
            } @else {
              <div class="numeros">
                <div class="numero">
                  <span class="valor">{{ r.cobrancas_enviadas }}</span>
                  <span class="chave">Cobranças enviadas</span>
                </div>
                <div class="numero">
                  <span class="valor">{{ r.pagamentos }}</span>
                  <span class="chave">Pagamentos</span>
                </div>
                <div class="numero">
                  <span class="valor dinheiro">{{ dinheiro(r.valor_recebido) }}</span>
                  <span class="chave">Valor recebido</span>
                </div>
                <div class="numero">
                  <span class="valor">{{ r.sem_resposta }}</span>
                  <span class="chave">Sem resposta</span>
                </div>
              </div>

              <h4>Respostas recebidas</h4>
              @for (chave of chaves(r); track chave) {
                <div class="resposta">
                  <span>{{ r.rotulos[chave] }}</span>
                  <strong>{{ r.respostas[chave] }}</strong>
                </div>
              }

              @if (r.cobrancas_falharam > 0) {
                <p class="nota alerta">
                  <mat-icon inline>warning</mat-icon>
                  {{ r.cobrancas_falharam }} mensagem(ns) não foram entregues.
                </p>
              }
            }
            }
          }
        </mat-card>
      }
    </div>
  `,
  styles: [`
    h2 { margin: 0; }
    h3 { margin: 0 0 8px; color: var(--lilas-300); }
    h4 { margin: 18px 0 6px; font-size: 0.95rem; }
    .campo-email { width: 260px; margin-bottom: -1.25em; }
    .campo-dia { width: 190px; margin-bottom: -1.25em; }

    .cabecalho-resumo {
      display: flex; align-items: flex-start; justify-content: space-between;
      gap: 16px; flex-wrap: wrap;
    }
    .ferramentas { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
    .janela { margin: 0 0 12px; }

    /* Os números primeiro, grandes: é o que a pessoa abre a tela para ver. */
    .numeros {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 12px; margin-top: 8px;
    }
    .numero {
      display: flex; flex-direction: column; gap: 2px;
      padding: 12px 14px; border-radius: var(--raio-interno);
      background: rgba(201, 169, 255, 0.10); border: 1px solid rgba(93, 64, 128, 0.14);
    }
    .numero .valor {
      font-size: 1.5rem; font-weight: 600; color: var(--lilas-300);
      letter-spacing: -0.02em; font-variant-numeric: tabular-nums;
    }
    .numero .valor.dinheiro { font-size: 1.25rem; }
    .numero .chave { font-size: 0.78rem; color: var(--texto-suave); }

    .resposta {
      display: flex; justify-content: space-between; gap: 12px;
      padding: 8px 2px; border-bottom: 1px solid var(--borda); font-size: 0.92rem;
    }
    .resposta:last-of-type { border-bottom: none; }
    .resposta strong { font-variant-numeric: tabular-nums; }

    .vazio { color: var(--texto-fraco); font-style: italic; margin: 8px 0 0; }
    .nota.alerta { color: var(--alerta); }
  `],
})
export class ConfigResumoComponent implements OnInit {
  private service = inject(ConfiguracoesService);
  private aviso = inject(MatSnackBar);

  config: Configuracao | null = null;
  /** Cópia do que veio do servidor, para o Cancelar ter a que voltar. */
  private original: Configuracao | null = null;
  private horarioOriginal = '20:00';
  horario = '20:00';
  readonly horarios = HORARIOS;
  readonly carregando = signal<boolean>(true);
  readonly salvando = signal<boolean>(false);

  readonly dias = signal<string[]>([]);
  diaEscolhido = '';
  readonly resumo = signal<ResumoDoDia | null>(null);
  readonly carregandoResumo = signal<boolean>(true);
  readonly exportando = signal<boolean>(false);

  /** O campo de e-mail só aparece quando o e-mail foi escolhido.
   *
   *  É método, não `computed`: a configuração é um objeto comum, alterado pelo
   *  ngModel, e `computed` só reage a sinais. Como método, o Angular reavalia
   *  a cada verificação e a tela acompanha a escolha.
   */
  querWhatsapp(): boolean {
    const canal = this.config?.canal_resumo;
    return canal === 'whatsapp' || canal === 'ambos';
  }

  /** Há algo diferente do que veio do servidor? Sem isso, os botões ficariam
   *  ativos o tempo todo e "Cancelar" não teria sentido visível. */
  mudou(): boolean {
    if (!this.config || !this.original) return false;
    return this.config.resumo_ativo !== this.original.resumo_ativo
      || this.horario !== this.horarioOriginal
      || this.config.canal_resumo !== this.original.canal_resumo
      || (this.config.email_resumo ?? '') !== (this.original.email_resumo ?? '')
      || (this.config.whatsapp_resumo ?? '') !== (this.original.whatsapp_resumo ?? '');
  }

  cancelar(): void {
    if (this.original) this.guardar(this.original);
  }

  private guardar(c: Configuracao): void {
    this.original = { ...c };
    this.config = { ...c };
    this.horario = (c.horario_resumo ?? '20:00:00').slice(0, 5);
    this.horarioOriginal = this.horario;
  }

  querEmail(): boolean {
    const canal = this.config?.canal_resumo;
    return canal === 'email' || canal === 'ambos';
  }

  ngOnInit(): void {
    this.service.obter().subscribe({
      next: (c) => {
        this.guardar(c);
        this.carregando.set(false);
      },
      error: () => {
        this.carregando.set(false);
        this.aviso.open('Erro ao carregar as configurações.', 'OK', { duration: 4000 });
      },
    });

    // A janela de dias vem do servidor: é ele quem define a regra dos 7 dias,
    // e repetir essa conta aqui abriria espaço para os dois discordarem.
    this.service.diasDoResumo().subscribe({
      next: (dias) => {
        this.dias.set(dias);
        this.diaEscolhido = dias[0] ?? '';
        this.carregarResumo();
      },
      error: () => this.carregandoResumo.set(false),
    });
  }

  carregarResumo(): void {
    if (!this.diaEscolhido) return;
    this.carregandoResumo.set(true);
    this.service.resumoDoDia(this.diaEscolhido).subscribe({
      next: (r) => { this.resumo.set(r); this.carregandoResumo.set(false); },
      error: () => {
        this.carregandoResumo.set(false);
        this.aviso.open('Não foi possível carregar o resumo desse dia.', 'OK',
                        { duration: 4000 });
      },
    });
  }

  exportar(): void {
    if (!this.diaEscolhido) return;
    this.exportando.set(true);
    this.service.resumoEmPdf(this.diaEscolhido).subscribe({
      next: (arquivo) => {
        this.exportando.set(false);
        const url = URL.createObjectURL(arquivo);
        const link = document.createElement('a');
        link.href = url;
        link.download = `resumo-${this.diaEscolhido}.pdf`;
        link.click();
        URL.revokeObjectURL(url);
      },
      error: () => {
        this.exportando.set(false);
        this.aviso.open('Não foi possível gerar o PDF.', 'OK', { duration: 4000 });
      },
    });
  }

  salvar(): void {
    if (!this.config) return;
    if (this.querEmail() && !this.config.email_resumo) {
      this.aviso.open('Informe o e-mail que vai receber o resumo.', 'OK', { duration: 4000 });
      return;
    }
    this.salvando.set(true);
    // Só os campos desta tela: mandar o resto sobrescreveria, com valores
    // velhos, o que a pessoa acabou de mudar em outra tela.
    this.service.salvar({
      resumo_ativo: this.config.resumo_ativo,
      horario_resumo: `${this.horario}:00`,
      canal_resumo: this.config.canal_resumo,
      email_resumo: this.config.email_resumo || undefined,
      whatsapp_resumo: this.config.whatsapp_resumo || undefined,
    }).subscribe({
      next: (salvo) => {
        this.salvando.set(false);
        this.guardar(salvo);
        this.aviso.open('Configurações salvas', 'OK', { duration: 3000 });
      },
      error: (erro) => {
        this.salvando.set(false);
        if (bloqueadoPorAssinatura(erro)) return;
        this.aviso.open('Erro ao salvar. Confira os valores e tente de novo.', 'OK',
                        { duration: 4000 });
      },
    });
  }

  chaves(r: ResumoDoDia): string[] { return Object.keys(r.rotulos); }

  dinheiro(v: number): string { return 'R$ ' + v.toFixed(2).replace('.', ','); }

  rotuloDia(iso: string): string {
    const hoje = this.dias()[0];
    const ontem = this.dias()[1];
    const [a, m, d] = iso.split('-');
    const formatada = `${d}/${m}`;
    if (iso === hoje) return `Hoje, ${formatada}`;
    if (iso === ontem) return `Ontem, ${formatada}`;
    return formatada;
  }
}
