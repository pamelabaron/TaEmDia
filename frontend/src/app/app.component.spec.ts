import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

import { AppComponent } from './app.component';

/**
 * Este arquivo era o modelo que o Angular cria junto com o projeto: procurava
 * um "Hello, taemdia-web" apagado no primeiro dia. Ficou quebrado por meses
 * sem ninguém perceber, porque o CI compilava o site mas não rodava teste
 * nenhum. Agora testa a barra lateral de verdade.
 */
describe('AppComponent', () => {
  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        provideNoopAnimations(),
      ],
    }).compileComponents();
  });

  it('é criado sem erro', () => {
    const fixture = TestBed.createComponent(AppComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('tem o menu da barra lateral com endereço e título em cada item', () => {
    const app = TestBed.createComponent(AppComponent).componentInstance;

    expect(app.menu.length).toBeGreaterThan(0);
    app.menu.forEach((item) => {
      expect(item.rota.startsWith('/')).toBeTrue();
      expect(item.titulo.length).toBeGreaterThan(0);
      expect(item.icone.length).toBeGreaterThan(0);
    });
  });

  it('nenhum endereço do menu passa por /configuracoes', () => {
    // A tela única de configurações virou uma tela por assunto. O endereço
    // antigo continua redirecionando, mas ninguém deve apontar para ele.
    const app = TestBed.createComponent(AppComponent).componentInstance;
    app.menu.forEach((item) => {
      expect(item.rota).not.toContain('configuracoes');
    });
  });

  it('a barra começa aberta e alterna quando pedem', () => {
    const app = TestBed.createComponent(AppComponent).componentInstance;

    expect(app.encolhida()).toBeFalse();
    app.alternarBarra();
    expect(app.encolhida()).toBeTrue();
    app.alternarBarra();
    expect(app.encolhida()).toBeFalse();
  });

  it('lembra da barra encolhida na próxima visita', () => {
    const primeira = TestBed.createComponent(AppComponent).componentInstance;
    primeira.alternarBarra();
    expect(primeira.encolhida()).toBeTrue();

    // Um segundo componente representa a página recarregada.
    const segunda = TestBed.createComponent(AppComponent).componentInstance;
    expect(segunda.encolhida()).toBeTrue();
  });
});
