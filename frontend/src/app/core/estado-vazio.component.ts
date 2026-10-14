import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';

/**
 * O que a tela mostra quando ainda não há nada nela.
 *
 * A conta nova é a primeira coisa que qualquer pessoa vê, e era o estado menos
 * cuidado do sistema: uma linha de texto cinza, "Nenhum cliente cadastrado
 * ainda", centralizada. Ela informa, mas não ensina. Quem acabou de entrar
 * quer saber o que fazer, não o que não existe.
 *
 * Então cada tela vazia diz três coisas, nesta ordem: o que é este lugar, o
 * que vai aparecer aqui, e qual é o próximo passo. O texto é escrito tela a
 * tela: "Nenhum resultado encontrado" serve para qualquer sistema do mundo, e
 * é exatamente por isso que não serve para nenhum.
 *
 * Sem ilustração nem ícone grande: desenho de catálogo no meio de uma tela
 * vazia é enfeite ocupando o lugar da instrução.
 */
@Component({
  selector: 'app-estado-vazio',
  standalone: true,
  imports: [MatButtonModule],
  template: `
    <div class="vazio" data-estado="vazio">
      <h3>{{ titulo }}</h3>
      <p>{{ texto }}</p>
      @if (acao) {
        <button mat-flat-button color="primary" (click)="aoAgir.emit()">
          {{ acao }}
        </button>
      }
    </div>
  `,
  styles: [`
    .vazio {
      /* Alinhado à esquerda, com um filete em cima: o mesmo tratamento das
         listas do sistema. Bloco centralizado no vazio parece aviso de erro. */
      border-top: 1px solid rgba(201, 169, 255, 0.14);
      padding: 42px 4px 46px;
      max-width: 34em;
    }
    h3 {
      font-size: 1.22rem; margin: 0 0 8px;
      letter-spacing: -0.018em; color: var(--texto);
    }
    p {
      margin: 0; font-size: 0.95rem; line-height: 1.6;
      color: var(--texto-suave);
    }
    button { margin-top: 22px; }
  `],
})
export class EstadoVazioComponent {
  /** O que é este lugar. Nomeia a coisa, não o fato de estar vazio. */
  @Input({ required: true }) titulo = '';
  /** O que vai aparecer aqui, e de onde vem. */
  @Input({ required: true }) texto = '';
  /** O próximo passo. Vazio quando não há ação possível a partir daqui. */
  @Input() acao = '';
  @Output() aoAgir = new EventEmitter<void>();
}
