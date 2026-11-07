import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

import { TELAS, TelaDeTeste } from './telas.fixtures';

/**
 * Hierarquia: o que a tela diz que é mais importante.
 *
 * Dois sinais de interface montada no automático, e os dois são a mesma falha
 * vista de ângulos diferentes: nada se destaca.
 *
 * - **Cartões de igual peso.** Quatro números do mesmo tamanho dizem que
 *   existem quatro números, não qual deles pede ação. Quem abre um sistema de
 *   cobrança quer saber de uma coisa antes das outras: quanto está atrasado.
 * - **Ações de igual peso.** Quando todo botão é o botão principal, nenhum é.
 *   A tela vira um menu indiferenciado, e a pessoa precisa ler tudo para
 *   descobrir o que fazer primeiro.
 *
 * Isto se mede: tamanho de fonte renderizado e contagem de botões primários.
 * Olhar a tela e achar que "está bom" não é medir.
 */

function montar(tela: TelaDeTeste) {
  TestBed.configureTestingModule({
    imports: [tela.componente],
    providers: [
      provideRouter([]),
      provideHttpClient(),
      provideHttpClientTesting(),
      provideNoopAnimations(),
      {
        provide: ActivatedRoute,
        useValue: { snapshot: { paramMap: convertToParamMap(tela.rota ?? {}) } },
      },
    ],
  });

  const http = TestBed.inject(HttpTestingController);
  const fixture = TestBed.createComponent(tela.componente);
  fixture.detectChanges();

  for (const [caminho, corpo] of tela.cheia) {
    http.match((r) => r.url.split('?')[0].endsWith(caminho))
        .forEach((p) => p.flush(corpo as object));
  }
  http.match(() => true).forEach((p) => p.flush([]));
  fixture.detectChanges();

  return fixture;
}

const PAINEL = TELAS.find((t) => t.nome === 'Painel')!;

describe('Hierarquia', () => {
  it('o painel tem um número que domina os outros', () => {
    const fixture = montar(PAINEL);

    const tamanhos = Array.from(fixture.nativeElement.querySelectorAll('.kpi .valor'))
      .map((e) => parseFloat(getComputedStyle(e as Element).fontSize));

    expect(tamanhos.length).withContext('o painel não tem cartões de número').toBeGreaterThan(2);

    const maior = Math.max(...tamanhos);
    const resto = tamanhos.filter((t) => t !== maior);

    expect(maior)
      .withContext(
        `todos os números têm quase o mesmo tamanho (${tamanhos.join(', ')}px), `
        + 'então a tela não diz qual olhar primeiro',
      )
      .toBeGreaterThan(Math.max(...resto) * 1.4);
  });

  it('o número que domina é o que o painel já elegeu', () => {
    // "Total a receber" é o destaque desde que o painel existe: é o único
    // cartão escuro e o único de coluna larga. Este teste trava essa escolha
    // em vez de propor outra, para que o destaque não mude por descuido.
    const fixture = montar(PAINEL);

    const cartoes = Array.from(fixture.nativeElement.querySelectorAll('.kpi')) as Element[];
    const maior = cartoes.reduce((a, b) => {
      const tamanho = (el: Element) =>
        parseFloat(getComputedStyle(el.querySelector('.valor')!).fontSize);
      return tamanho(a) >= tamanho(b) ? a : b;
    });

    expect(maior.classList.contains('receber'))
      .withContext('o cartão em destaque deveria ser o do total a receber')
      .toBeTrue();
  });

  it('o número principal não estoura o cartão na tela mais estreita', () => {
    // Aumentar um número é fácil; o que quebra é o valor comprido num celular
    // de 320px. "R$ 148.820,50" tem treze caracteres, e é o caso real de quem
    // tem carteira grande.
    const fixture = montar(PAINEL);
    const cartao = fixture.nativeElement.querySelector('.kpi.receber') as HTMLElement;
    const valor = cartao.querySelector('.valor') as HTMLElement;

    valor.textContent = 'R$ 148.820,50';
    cartao.style.width = '288px';   // 320px de tela, menos a margem da página
    fixture.detectChanges();

    expect(valor.scrollWidth)
      .withContext(`o valor ocupa ${valor.scrollWidth}px num cartão de ${cartao.clientWidth}px`)
      .toBeLessThanOrEqual(cartao.clientWidth);
  });

  TELAS.forEach((tela) => {
    it(`"${tela.nome}" tem no máximo uma ação principal visível`, () => {
      const fixture = montar(tela);

      // Só botão. O Material põe a mesma classe de cor no campo de formulário
      // em foco, e a primeira versão deste teste acusava "Título" e "E-mail"
      // como se fossem ações.
      const primarios = Array.from(
        fixture.nativeElement.querySelectorAll(
          'button.mat-primary, button[color="primary"], a.mat-primary',
        ),
      ).filter((e) => {
        const el = e as HTMLElement;
        return el.offsetParent !== null || el.getClientRects().length > 0;
      });

      expect(primarios.length)
        .withContext(
          `"${tela.nome}" mostra ${primarios.length} botões principais ao mesmo tempo: `
          + primarios.map((e) => (e as HTMLElement).innerText.trim().slice(0, 24)).join(' | '),
        )
        .toBeLessThanOrEqual(1);
    });
  });
});
