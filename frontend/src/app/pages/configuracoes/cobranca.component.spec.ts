import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

import { ConfigCobrancaComponent } from './cobranca.component';

/**
 * A tela de cobrança automática tem duas regras que não se veem olhando:
 *
 * 1. Salvar e Cancelar só acendem quando algo mudou. Botão sempre aceso faz a
 *    pessoa salvar sem querer e não deixa claro que há alteração pendente.
 * 2. Salvar manda só os campos desta tela. Mandar o resto sobrescreveria, com
 *    valores velhos, o que ela acabou de mudar em outra tela de configuração.
 */
describe('ConfigCobrancaComponent', () => {
  let http: HttpTestingController;

  const VINDO_DO_SERVIDOR = {
    id: 'cfg1',
    envio_auto_global: true,
    dias_antecedencia_lembrete: 3,
    horario_resumo: '20:00',
    resumo_ativo: true,
    canal_resumo: 'whatsapp',
    email_resumo: null,
    whatsapp_resumo: null,
  };

  function abrir() {
    const fixture = TestBed.createComponent(ConfigCobrancaComponent);
    fixture.detectChanges();
    http.expectOne((r) => r.url.endsWith('/configuracoes')).flush({ ...VINDO_DO_SERVIDOR });
    return fixture.componentInstance;
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ConfigCobrancaComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideNoopAnimations()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('carrega as configurações ao abrir', () => {
    const c = abrir();
    expect(c.carregando()).toBeFalse();
    expect(c.config?.dias_antecedencia_lembrete).toBe(3);
  });

  it('os botões nascem apagados, porque nada mudou ainda', () => {
    expect(abrir().mudou()).toBeFalse();
  });

  it('acende os botões quando o envio automático é desligado', () => {
    const c = abrir();
    c.config!.envio_auto_global = false;
    expect(c.mudou()).toBeTrue();
  });

  it('acende os botões quando os dias mudam', () => {
    const c = abrir();
    c.config!.dias_antecedencia_lembrete = 5;
    expect(c.mudou()).toBeTrue();
  });

  it('não confunde o número 3 com o texto "3"', () => {
    // O campo do formulário devolve texto. Sem a conversão, digitar o mesmo
    // valor de novo acenderia os botões sem nada ter mudado.
    const c = abrir();
    c.config!.dias_antecedencia_lembrete = '3' as unknown as number;
    expect(c.mudou()).toBeFalse();
  });

  it('Cancelar volta ao que veio do servidor', () => {
    const c = abrir();
    c.config!.envio_auto_global = false;
    c.config!.dias_antecedencia_lembrete = 10;

    c.cancelar();

    expect(c.config?.envio_auto_global).toBeTrue();
    expect(c.config?.dias_antecedencia_lembrete).toBe(3);
    expect(c.mudou()).toBeFalse();
  });

  it('manda só os campos desta tela, e não a configuração inteira', () => {
    const c = abrir();
    c.config!.dias_antecedencia_lembrete = 7;

    c.salvar();

    const req = http.expectOne((r) => r.method === 'PATCH' && r.url.endsWith('/configuracoes'));
    expect(Object.keys(req.request.body).sort())
      .toEqual(['dias_antecedencia_lembrete', 'envio_auto_global']);
    expect(req.request.body.dias_antecedencia_lembrete).toBe(7);

    req.flush({ ...VINDO_DO_SERVIDOR, dias_antecedencia_lembrete: 7 });
    // Depois de salvar, o que está na tela passa a ser o novo original.
    expect(c.mudou()).toBeFalse();
    expect(c.salvando()).toBeFalse();
  });

  it('devolve o botão quando o servidor recusa', () => {
    const c = abrir();
    c.config!.dias_antecedencia_lembrete = 7;

    c.salvar();
    http.expectOne((r) => r.method === 'PATCH')
      .flush({ detail: 'erro' }, { status: 500, statusText: 'Erro' });

    // Quem foi barrado também precisa poder tentar de novo.
    expect(c.salvando()).toBeFalse();
    expect(c.mudou()).toBeTrue();
  });

  it('a recusa por assinatura não vira "erro ao salvar"', () => {
    const c = abrir();
    c.config!.dias_antecedencia_lembrete = 7;

    c.salvar();
    http.expectOne((r) => r.method === 'PATCH')
      .flush({ detail: 'assinatura' }, { status: 402, statusText: 'Payment Required' });

    expect(c.salvando()).toBeFalse();
  });
});
