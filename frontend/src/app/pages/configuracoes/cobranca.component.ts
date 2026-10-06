import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Configuracao, ConfiguracoesService } from '../../core/configuracoes.service';
import { bloqueadoPorAssinatura } from '../../core/erros';

/** Como e quando o sistema cobra sozinho. */
@Component({
  selector: 'app-config-cobranca',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatButtonModule, MatIconModule, MatFormFieldModule,
    MatInputModule, MatSlideToggleModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="pagina-config">
      <h2>Cobrança automática</h2>
      <p class="ajuda">Quando o sistema envia as mensagens sem você precisar lembrar.</p>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        @if (config; as c) {
          <mat-card class="bloco">
            <div class="linha">
              <div class="texto">
                <span class="rotulo">Enviar cobranças automaticamente</span>
                <span class="descricao">
                  Quando ligado, o sistema envia as mensagens sozinho nas datas certas.
                  Desligue para cobrar apenas manualmente.
                </span>
              </div>
              <mat-slide-toggle [(ngModel)]="c.envio_auto_global" name="envioAuto">
              </mat-slide-toggle>
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
              As cobranças automáticas respeitam o horário comercial (08h às 20h) e o limite
              de 3 mensagens por dia para cada cliente.
            </p>
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
      }
    </div>
  `,
  styles: [`h2 { margin: 0; }`],
})
export class ConfigCobrancaComponent implements OnInit {
  private service = inject(ConfiguracoesService);
  private aviso = inject(MatSnackBar);

  config: Configuracao | null = null;
  /** Cópia do que veio do servidor, para o Cancelar ter a que voltar. */
  private original: Configuracao | null = null;
  readonly carregando = signal<boolean>(true);
  readonly salvando = signal<boolean>(false);

  ngOnInit(): void {
    this.service.obter().subscribe({
      next: (c) => { this.guardar(c); this.carregando.set(false); },
      error: () => {
        this.carregando.set(false);
        this.aviso.open('Erro ao carregar as configurações.', 'OK', { duration: 4000 });
      },
    });
  }

  /** Há algo diferente do que veio do servidor? Sem isso, os botões ficariam
   *  ativos o tempo todo e "Cancelar" não teria sentido visível. */
  mudou(): boolean {
    if (!this.config || !this.original) return false;
    return this.config.envio_auto_global !== this.original.envio_auto_global
      || Number(this.config.dias_antecedencia_lembrete)
         !== Number(this.original.dias_antecedencia_lembrete);
  }

  cancelar(): void {
    if (this.original) this.guardar(this.original);
  }

  private guardar(c: Configuracao): void {
    this.original = { ...c };
    this.config = { ...c };
  }

  salvar(): void {
    if (!this.config) return;
    this.salvando.set(true);
    // Envia só o que esta tela controla: mandar o resto sobrescreveria, com
    // valores velhos, o que a pessoa acabou de mudar na outra tela.
    this.service.salvar({
      envio_auto_global: this.config.envio_auto_global,
      dias_antecedencia_lembrete: Number(this.config.dias_antecedencia_lembrete),
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
}
