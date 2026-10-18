import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';

/**
 * O que a tela mostra quando não conseguiu carregar.
 *
 * Antes isto era uma tarja preta que subia escrito "Erro ao carregar clientes"
 * e sumia em quatro segundos. Três problemas de uma vez: ela some sozinha, e
 * quem estava olhando para outro canto perde o aviso; o que sobra é uma tela
 * em branco idêntica à de quem não tem nenhum cliente; e a frase não diz nem o
 * que houve nem o que fazer.
 *
 * O erro agora fica no lugar do conteúdo, parado, com um caminho de volta.
 * A tarja continua existindo, mas só para erro de **ação** (salvar, cancelar),
 * onde a tela já tem conteúdo e ninguém ficou sem nada.
 */
@Component({
  selector: 'app-estado-erro',
  standalone: true,
  imports: [MatButtonModule],
  template: `
    <div class="erro" data-estado="erro">
      <h3>{{ titulo }}</h3>
      <p>{{ texto }}</p>
      <button mat-stroked-button (click)="aoTentar.emit()">Tentar de novo</button>
    </div>
  `,
  styles: [`
    .erro {
      /* O filete em cima é da cor de alerta, não de perigo: não conseguir
         carregar é contratempo, não perda de dado. Vermelho aqui assustaria
         sem motivo. */
      border-top: 2px solid var(--alerta);
      padding: 38px 4px 42px;
      max-width: 34em;
    }
    h3 {
      font-size: 1.18rem; margin: 0 0 8px;
      letter-spacing: -0.018em; color: var(--texto);
    }
    p {
      margin: 0; font-size: 0.95rem; line-height: 1.6;
      color: var(--texto-suave);
    }
    button { margin-top: 20px; }
  `],
})
export class EstadoErroComponent {
  /** O que houve, em linguagem de quem usa. */
  @Input() titulo = 'Não deu para carregar';
  /**
   * O que fazer, e o que não aconteceu de ruim. A segunda parte importa:
   * quem vê um erro num sistema de cobrança pensa primeiro que perdeu dado.
   */
  @Input() texto = 'Pode ter sido a conexão. Nada do que estava salvo se perdeu.';
  @Output() aoTentar = new EventEmitter<void>();
}
