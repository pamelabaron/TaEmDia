import { Component, Input, numberAttribute } from '@angular/core';

/**
 * O que a tela mostra enquanto os dados não chegaram.
 *
 * Antes era uma roda girando, a mesma em todas as telas. A roda diz "espere",
 * e só. Não diz o que está vindo nem quanto espaço vai ocupar, então a página
 * salta quando o conteúdo entra.
 *
 * O esqueleto desenha a forma do que está chegando: linhas onde virão linhas,
 * blocos onde virão números. Quem olha já sabe o que esperar, e o conteúdo
 * entra no lugar onde a mancha já estava, sem empurrar nada.
 *
 * O brilho que percorre as barras é desligado para quem pediu menos
 * movimento no sistema (`prefers-reduced-motion`).
 */
@Component({
  selector: 'app-esqueleto',
  standalone: true,
  template: `
    <div class="esqueleto" data-estado="carregando" aria-busy="true"
         [attr.aria-label]="rotulo">
      @for (linha of repeticoes(); track $index) {
        <div class="barra" [class.bloco]="tipo === 'blocos'"></div>
      }
    </div>
  `,
  styles: [`
    .esqueleto { display: grid; gap: 12px; }
    .esqueleto:has(.bloco) {
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 16px;
    }
    .barra {
      height: 18px; border-radius: 6px;
      background-color: rgba(201, 169, 255, 0.07);
      background-image: linear-gradient(
        100deg,
        rgba(201, 169, 255, 0.00) 20%,
        rgba(201, 169, 255, 0.13) 50%,
        rgba(201, 169, 255, 0.00) 80%
      );
      background-size: 240% 100%;
      animation: correr 1500ms ease-in-out infinite;
    }
    /* Larguras diferentes: barra toda igual lê como tabela, não como texto. */
    .barra:nth-child(3n + 2) { width: 86%; }
    .barra:nth-child(3n + 3) { width: 68%; }
    .barra.bloco { height: 92px; width: auto; border-radius: var(--raio); }

    @keyframes correr {
      from { background-position: 180% 0; }
      to   { background-position: -60% 0; }
    }
    @media (prefers-reduced-motion: reduce) {
      .barra { animation: none; }
    }
  `],
})
export class EsqueletoComponent {
  /** "lista" para linhas de texto, "blocos" para cartões de número. */
  @Input() tipo: 'lista' | 'blocos' = 'lista';
  /** Quantas formas desenhar. O padrão cobre a primeira dobra da tela.
   *  Com `numberAttribute`, o template pode escrever quantidade="5" sem
   *  colchetes, que é como se escreve atributo em todo o resto do projeto. */
  @Input({ transform: numberAttribute }) quantidade = 4;
  /** O que está vindo, para quem usa leitor de tela. */
  @Input() rotulo = 'Carregando';

  repeticoes(): number[] {
    return Array.from({ length: this.quantidade }, (_, i) => i);
  }
}
