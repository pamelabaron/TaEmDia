import { Component } from '@angular/core';
import { MinhaAssinaturaComponent } from './minha-assinatura.component';

/** Tela própria da assinatura. O cartão já existia; aqui ele ganha título e
 *  endereço, para o menu da pessoa levar direto ao assunto. */
@Component({
  selector: 'app-pagina-assinatura',
  standalone: true,
  imports: [MinhaAssinaturaComponent],
  template: `
    <div class="pagina-config">
      <h2>Minha assinatura</h2>
      <p class="ajuda">Situação, pagamento e histórico dos comprovantes enviados.</p>
      <app-minha-assinatura />
    </div>
  `,
  styles: [`h2 { margin: 0; }`],
})
export class PaginaAssinaturaComponent {}
