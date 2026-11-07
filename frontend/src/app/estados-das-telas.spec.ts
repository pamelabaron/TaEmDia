import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

import { TELAS, TelaDeTeste } from './telas.fixtures';

/**
 * Toda tela precisa de três estados desenhados, não só o estado cheio.
 *
 * O estado cheio é o fácil: é o que se vê enquanto se constrói, com dados de
 * exemplo na tela. Os outros três aparecem na vida real e costumam ficar de
 * fora:
 *
 * - **vazio**, que é a primeira coisa que uma conta nova vê. Uma linha de
 *   texto cinza dizendo "Nenhum cliente cadastrado ainda" não ensina o próximo
 *   passo: a pessoa entrou para usar o sistema e a tela não diz como começar.
 * - **erro**, que hoje é uma tarja que sobe e some em quatro segundos. Quando
 *   ela some, sobra uma tela em branco e nenhuma pista do que fazer.
 * - **carregando**, que é uma roda girando igual em toda tela, sem dizer o que
 *   está vindo nem quanto ocupa.
 *
 * A pesquisa sobre interface gerada por máquina aponta justamente isso: o
 * caminho feliz é desenhado, os outros três ficam no padrão de fábrica.
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
  return { fixture, http };
}

/** Responde o que a tela pediu, comparando só o caminho (sem parâmetros). */
function responder(http: HttpTestingController, respostas: [string, unknown][]) {
  for (const [caminho, corpo] of respostas) {
    http.match((r) => r.url.split('?')[0].endsWith(caminho))
        .forEach((p) => p.flush(corpo as object));
  }
  http.match(() => true).forEach((p) => p.flush([]));
}

function recusar(http: HttpTestingController) {
  http.match(() => true).forEach((p) =>
    p.flush({ detail: 'erro' }, { status: 500, statusText: 'Erro do servidor' }));
}

function texto(el: Element | null): string {
  return (el?.textContent ?? '').trim();
}

describe('Estados das telas', () => {
  afterEach(() => {
    const http = TestBed.inject(HttpTestingController);
    http.match(() => true).forEach((p) => p.flush([]));
  });

  TELAS.filter((t) => !t.eFormulario).forEach((tela) => {
    it(`"${tela.nome}" tem estado vazio desenhado`, () => {
      const { fixture, http } = montar(tela);
      responder(http, tela.vazia);
      fixture.detectChanges();

      const vazio = fixture.nativeElement.querySelector('[data-estado="vazio"]');

      expect(vazio)
        .withContext(`"${tela.nome}" não mostra nada quando a conta é nova`)
        .not.toBeNull();
      expect(texto(vazio.querySelector('h3')))
        .withContext('falta um título que diga o que é esta tela')
        .toBeTruthy();
      expect(texto(vazio.querySelector('p')))
        .withContext('falta uma frase explicando o que aparece aqui')
        .toBeTruthy();
    });
  });

  TELAS.forEach((tela) => {
    it(`"${tela.nome}" explica o erro e oferece saída`, () => {
      const { fixture, http } = montar(tela);
      recusar(http);
      fixture.detectChanges();

      const erro = fixture.nativeElement.querySelector('[data-estado="erro"]');

      expect(erro)
        .withContext(`"${tela.nome}" deixa a pessoa sem nada quando o servidor falha`)
        .not.toBeNull();
      expect(texto(erro.querySelector('button')))
        .withContext('falta o botão de tentar de novo')
        .toContain('Tentar de novo');
    });
  });

  TELAS.forEach((tela) => {
    it(`"${tela.nome}" mostra a forma do que está vindo`, () => {
      const { fixture } = montar(tela);
      // De propósito sem responder: é o instante em que a tela está esperando.

      expect(fixture.nativeElement.querySelector('[data-estado="carregando"]'))
        .withContext(`"${tela.nome}" não desenha o carregamento`)
        .not.toBeNull();
      expect(fixture.nativeElement.querySelector('mat-spinner'))
        .withContext('ainda usa a roda girando, igual em toda tela')
        .toBeNull();
    });
  });
});
