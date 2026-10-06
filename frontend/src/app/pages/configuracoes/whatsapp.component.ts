import { Component, OnInit, inject, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { CobrancasService, StatusWhatsApp } from '../../core/cobrancas.service';
import { bloqueadoPorAssinatura } from '../../core/erros';

/** Conexão do WhatsApp. Só isto: quem procura esta tela quer conectar ou conferir. */
@Component({
  selector: 'app-config-whatsapp',
  standalone: true,
  imports: [MatCardModule, MatButtonModule, MatIconModule],
  template: `
    <div class="pagina-config">
      <h2>WhatsApp</h2>
      <p class="ajuda">O número que envia as cobranças aos seus clientes.</p>

      <mat-card class="bloco">
        @if (bloqueado()) {
          <div class="linha">
            <div class="texto">
              <span class="rotulo">Disponível com assinatura ativa</span>
              <span class="descricao">
                Renove para conectar seu número e voltar a enviar cobranças.
              </span>
            </div>
          </div>
        } @else {
          @if (status(); as w) {
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
                <p class="descricao">
                  Abra o WhatsApp no celular, toque em Aparelhos conectados e escaneie:
                </p>
                <img [src]="w.qrcode" alt="QR Code para conectar o WhatsApp" />
              </div>
            }

            @if (w.conectado && !w.modo_simulador) {
              <div class="acoes">
                <button mat-stroked-button color="warn" (click)="desconectar()">
                  Desconectar
                </button>
              </div>
            }
          } @else {
            <p class="descricao">Verificando conexão…</p>
          }
        }
      </mat-card>
    </div>
  `,
  styles: [`
    h2 { margin: 0; }
    .bolinha { width: 12px; height: 12px; border-radius: 50%;
               background: var(--perigo); flex: none; }
    .bolinha.on { background: var(--sucesso); }
    .qr { text-align: center; padding: 12px 0; }
    .qr img { max-width: 240px; width: 100%; }
  `],
})
export class ConfigWhatsappComponent implements OnInit {
  private cobrancas = inject(CobrancasService);
  private aviso = inject(MatSnackBar);

  readonly status = signal<StatusWhatsApp | null>(null);
  /** O servidor respondeu 402: conectar o WhatsApp depende de assinatura ativa. */
  readonly bloqueado = signal<boolean>(false);

  ngOnInit(): void {
    this.carregar();
  }

  private carregar(): void {
    this.cobrancas.statusWhatsApp().subscribe({
      next: (w) => { this.status.set(w); this.bloqueado.set(false); },
      error: (erro) => {
        this.status.set(null);
        this.bloqueado.set(bloqueadoPorAssinatura(erro));
      },
    });
  }

  desconectar(): void {
    this.cobrancas.desconectarWhatsApp().subscribe({
      next: () => {
        this.aviso.open('WhatsApp desconectado.', 'OK', { duration: 3000 });
        this.carregar();
      },
      error: (erro) => {
        if (bloqueadoPorAssinatura(erro)) return;
        this.aviso.open('Erro ao desconectar.', 'OK', { duration: 4000 });
      },
    });
  }
}
