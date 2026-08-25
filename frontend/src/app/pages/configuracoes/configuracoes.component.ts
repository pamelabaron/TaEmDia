import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Configuracao, ConfiguracoesService } from '../../core/configuracoes.service';
import { CobrancasService, StatusWhatsApp } from '../../core/cobrancas.service';

// Horários possíveis para o resumo diário (fim do dia, conforme o RFC).
const HORARIOS = ['18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00'];

@Component({
  selector: 'app-configuracoes',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatFormFieldModule, MatInputModule, MatSelectModule,
    MatButtonModule, MatIconModule, MatSlideToggleModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="pagina">
      <h2>Configurações</h2>
      <p class="ajuda">Ajuste como o sistema cobra seus clientes e como você recebe os avisos.</p>

      <mat-card class="bloco">
        <h3>WhatsApp</h3>
        @if (whats(); as w) {
          <div class="linha">
            <div class="texto">
              <span class="rotulo">
                @if (w.modo_simulador) { Modo simulador }
                @else if (w.conectado) { Conectado }
                @else { Não conectado }
              </span>
              <span class="descricao">{{ w.detalhe }}</span>
            </div>
            <span class="bolinha" [class.on]="w.conectado"></span>
          </div>
          @if (w.qrcode) {
            <div class="qr">
              <p class="descricao">Abra o WhatsApp no celular, toque em Aparelhos conectados e escaneie:</p>
              <img [src]="w.qrcode" alt="QR Code do WhatsApp" />
            </div>
          }
          @if (w.conectado && !w.modo_simulador) {
            <button mat-stroked-button color="warn" (click)="desconectar()">Desconectar</button>
          }
        } @else {
          <p class="descricao">Verificando conexão…</p>
        }
      </mat-card>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        @if (config; as c) {
          <mat-card class="bloco">
            <h3>Cobrança automática</h3>

            <div class="linha">
              <div class="texto">
                <span class="rotulo">Enviar cobranças automaticamente</span>
                <span class="descricao">
                  Quando ligado, o sistema envia as mensagens sozinho nas datas certas.
                  Desligue para cobrar apenas manualmente.
                </span>
              </div>
              <mat-slide-toggle [(ngModel)]="c.envio_auto_global" name="envioAuto"></mat-slide-toggle>
            </div>

            <div class="linha">
              <div class="texto">
                <span class="rotulo">Avisar antes do vencimento</span>
                <span class="descricao">Quantos dias antes o cliente recebe o lembrete.</span>
              </div>
              <mat-form-field appearance="outline" class="campo-curto">
                <mat-label>Dias</mat-label>
                <input matInput type="number" min="0" max="30"
                       [(ngModel)]="c.dias_antecedencia_lembrete" name="dias" />
              </mat-form-field>
            </div>

            <p class="nota">
              <mat-icon inline>info</mat-icon>
              As cobranças automáticas respeitam o horário comercial (08h às 20h).
            </p>
          </mat-card>

          <mat-card class="bloco">
            <h3>Resumo diário</h3>

            <div class="linha">
              <div class="texto">
                <span class="rotulo">Receber resumo diário</span>
                <span class="descricao">
                  Um resumo do dia (cobranças enviadas, pagamentos e respostas) no seu WhatsApp.
                </span>
              </div>
              <mat-slide-toggle [(ngModel)]="c.resumo_ativo" name="resumoAtivo"></mat-slide-toggle>
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
          </mat-card>

          <div class="acoes">
            <button mat-raised-button color="primary" [disabled]="salvando()" (click)="salvar()">
              <mat-icon>save</mat-icon> Salvar configurações
            </button>
          </div>
        }
      }
    </div>
  `,
  styles: [`
    .pagina { max-width: 720px; margin: 0 auto; padding: 16px; }
    .ajuda { color: #666; margin-bottom: 16px; }
    .centro { display: flex; justify-content: center; padding: 32px; }
    .bloco { padding: 16px 20px; margin-bottom: 16px; }
    .bloco h3 { margin: 0 0 8px; color: #1565c0; }
    .linha {
      display: flex; align-items: center; justify-content: space-between;
      gap: 16px; padding: 14px 0; border-bottom: 1px solid #eee;
    }
    .linha:last-of-type { border-bottom: none; }
    .texto { display: flex; flex-direction: column; }
    .rotulo { font-weight: 500; }
    .descricao { font-size: 0.8rem; color: #777; margin-top: 2px; }
    .campo-curto { width: 110px; margin-bottom: -1.25em; }
    .nota { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; color: #777; margin: 12px 0 0; }
    .acoes { display: flex; justify-content: flex-end; }
    @media (max-width: 600px) {
      .linha { flex-direction: column; align-items: flex-start; }
      .bolinha { width: 12px; height: 12px; border-radius: 50%; background: #c62828; flex: none; }
    .bolinha.on { background: #2e7d32; }
    .qr { text-align: center; padding: 12px 0; }
    .qr img { max-width: 240px; width: 100%; }
    .acoes button { width: 100%; }
    }
  `],
})
export class ConfiguracoesComponent implements OnInit {
  private service = inject(ConfiguracoesService);
  private snack = inject(MatSnackBar);
  private cobrancas = inject(CobrancasService);

  config: Configuracao | null = null;
  horario = '20:00';
  readonly horarios = HORARIOS;
  readonly carregando = signal<boolean>(true);
  readonly salvando = signal<boolean>(false);
  readonly whats = signal<StatusWhatsApp | null>(null);

  ngOnInit(): void {
    this.cobrancas.statusWhatsApp().subscribe({
      next: (w) => this.whats.set(w),
      error: () => this.whats.set(null),
    });
    this.service.obter().subscribe({
      next: (c) => {
        this.config = c;
        this.horario = (c.horario_resumo ?? '20:00:00').slice(0, 5);
        this.carregando.set(false);
      },
      error: () => {
        this.carregando.set(false);
        this.snack.open('Erro ao carregar as configurações.', 'OK', { duration: 4000 });
      },
    });
  }

  desconectar(): void {
    this.cobrancas.desconectarWhatsApp().subscribe({
      next: () => {
        this.snack.open("WhatsApp desconectado.", "OK", { duration: 3000 });
        this.cobrancas.statusWhatsApp().subscribe((w) => this.whats.set(w));
      },
      error: () => this.snack.open("Erro ao desconectar.", "OK", { duration: 4000 }),
    });
  }

  salvar(): void {
    if (!this.config) return;
    this.salvando.set(true);
    this.service.salvar({
      envio_auto_global: this.config.envio_auto_global,
      dias_antecedencia_lembrete: Number(this.config.dias_antecedencia_lembrete),
      resumo_ativo: this.config.resumo_ativo,
      horario_resumo: `${this.horario}:00`,
    }).subscribe({
      next: () => {
        this.salvando.set(false);
        this.snack.open('Configurações salvas!', 'OK', { duration: 3000 });
      },
      error: () => {
        this.salvando.set(false);
        this.snack.open('Erro ao salvar. Confira os valores e tente de novo.', 'OK', { duration: 4000 });
      },
    });
  }
}
