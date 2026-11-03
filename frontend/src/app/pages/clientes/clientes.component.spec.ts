import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

import { ClientesComponent } from './clientes.component';

/**
 * O cadastro de cliente é a porta de entrada do sistema: número errado aqui
 * vira cobrança que não chega. Estes testes cobrem a conferência que acontece
 * antes de a tela chamar a API (RN-C01 e RN-C02).
 *
 * A API confere de novo, e isso tem teste próprio em
 * backend/tests/test_api_clientes.py. Aqui o que importa é a tela não deixar
 * a pessoa esperar a viagem até o servidor para descobrir um dígito faltando.
 */
describe('ClientesComponent', () => {
  let http: HttpTestingController;

  function criar() {
    const fixture = TestBed.createComponent(ClientesComponent);
    // O ngOnInit só roda no primeiro ciclo de detecção, não na criação. Sem
    // esta linha a tela nem chega a pedir a lista.
    fixture.detectChanges();
    // A tela pede a lista assim que abre. Responder mantém o teste limpo.
    http.expectOne((r) => r.url.endsWith('/clientes')).flush([]);
    return fixture.componentInstance;
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ClientesComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        provideNoopAnimations(),
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('já abre com o 55 preenchido no código do país', () => {
    expect(criar().novo.codigo_pais).toBe('55');
  });

  it('não reclama enquanto o campo está vazio', () => {
    const c = criar();
    expect(c.erroTelefone()).toBe('');
    expect(c.erroCpf()).toBe('');
  });

  it('avisa que falta o DDD antes de chamar a API', () => {
    const c = criar();
    c.novo.whatsapp_numero = '999990000';
    expect(c.erroTelefone()).toContain('DDD');
  });

  it('mostra como o número vai ficar salvo', () => {
    const c = criar();
    c.novo.whatsapp_numero = '47999990000';
    expect(c.erroTelefone()).toBe('');
    expect(c.previaDoTelefone()).toContain('55 (47) 99999-0000');
  });

  it('avisa CPF inválido', () => {
    const c = criar();
    c.novo.cpf = '11111111111';
    expect(c.erroCpf()).toContain('CPF');
  });

  it('aceita CPF válido com pontuação', () => {
    const c = criar();
    c.novo.cpf = '529.982.247-25';
    expect(c.erroCpf()).toBe('');
  });

  it('não chama a API quando o telefone está errado', () => {
    const c = criar();
    c.novo.nome = 'Rosangela Ferreira';
    c.novo.whatsapp_numero = '999990000';

    c.salvar();

    // Se a tela tivesse chamado a API, o verify() do afterEach acusaria.
    expect(c.salvando()).toBeFalse();
  });

  it('não chama a API quando falta o nome', () => {
    const c = criar();
    c.novo.whatsapp_numero = '47999990000';

    c.salvar();

    expect(c.salvando()).toBeFalse();
  });

  it('manda o número já com o código do país', () => {
    const c = criar();
    c.novo.nome = 'Rosangela Ferreira';
    c.novo.whatsapp_numero = '(47) 99999-0000';
    c.novo.cpf = '529.982.247-25';

    c.salvar();

    const chamada = http.expectOne((r) => r.method === 'POST' && r.url.endsWith('/clientes'));
    expect(chamada.request.body.whatsapp_numero).toBe('5547999990000');
    expect(chamada.request.body.cpf).toBe('52998224725');
    expect(chamada.request.body.codigo_pais).toBe('55');

    chamada.flush({ id: '1' });
    http.expectOne((r) => r.url.endsWith('/clientes')).flush([]);
  });

  it('manda CPF nulo quando o campo fica em branco', () => {
    const c = criar();
    c.novo.nome = 'Rosangela Ferreira';
    c.novo.whatsapp_numero = '47999990000';

    c.salvar();

    const chamada = http.expectOne((r) => r.method === 'POST' && r.url.endsWith('/clientes'));
    expect(chamada.request.body.cpf).toBeNull();

    chamada.flush({ id: '1' });
    http.expectOne((r) => r.url.endsWith('/clientes')).flush([]);
  });
});
