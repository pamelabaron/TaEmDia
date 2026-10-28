import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Router } from '@angular/router';

import { API_URL } from './api.config';
import { AssinaturaService } from './assinatura.service';
import { AuthService } from './auth.service';
import { ClientesService } from './clientes.service';
import { CobrancasService } from './cobrancas.service';
import { ConfiguracoesService } from './configuracoes.service';
import { DashboardService } from './dashboard.service';
import { RankingService } from './ranking.service';
import { TemplatesService } from './templates.service';
import { VendasService } from './vendas.service';

/**
 * Os serviços são a fronteira entre o site e a API: cada método vira uma
 * chamada HTTP. O que quebra aqui é endereço errado e verbo errado, e isso
 * não aparece ao olhar a tela: a chamada sai, volta 404, e a pessoa lê um
 * "erro ao carregar" genérico.
 *
 * Foi exatamente o que aconteceu quando a API mudou para /api e cinco telas
 * passaram a bater no lugar errado. Estes testes conferem o endereço.
 */
describe('Serviços da API', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  /** Confere endereço e verbo de uma chamada, e responde para ela terminar. */
  function conferir(metodo: string, caminho: string, resposta: Object = {}) {
    const req = http.expectOne(`${API_URL}${caminho}`);
    expect(req.request.method).toBe(metodo);
    req.flush(resposta);
    return req;
  }

  describe('ClientesService', () => {
    it('lista pelo endereço certo', () => {
      TestBed.inject(ClientesService).listar().subscribe();
      conferir('GET', '/clientes', []);
    });

    it('cadastra por POST', () => {
      const dados = { nome: 'Rosangela Ferreira', whatsapp_numero: '5547999990000' };
      TestBed.inject(ClientesService).criar(dados).subscribe();
      const req = conferir('POST', '/clientes');
      expect(req.request.body).toEqual(dados);
    });
  });

  describe('VendasService', () => {
    it('busca o perfil do cliente', () => {
      TestBed.inject(VendasService).perfil('abc').subscribe();
      conferir('GET', '/clientes/abc/perfil');
    });

    it('baixa a parcela por POST, não por GET', () => {
      // Pagar muda o estado: GET não poderia, e um navegador poderia repetir.
      TestBed.inject(VendasService).pagarParcela('p1').subscribe();
      conferir('POST', '/parcelas/p1/pagar');
    });

    it('cancela a venda', () => {
      TestBed.inject(VendasService).cancelarVenda('v1').subscribe();
      conferir('POST', '/vendas/v1/cancelar');
    });

    it('registra a venda', () => {
      const venda = {
        cliente_id: 'c1', valor_total: 300, num_parcelas: 3,
        data_primeira_parcela: '2026-10-05',
      };
      TestBed.inject(VendasService).registrarVenda(venda).subscribe();
      const req = conferir('POST', '/vendas');
      expect(req.request.body).toEqual(venda);
    });
  });

  describe('CobrancasService', () => {
    it('leva o período no endereço', () => {
      TestBed.inject(CobrancasService).listar('semana').subscribe();
      conferir('GET', '/cobrancas?periodo=semana', []);
    });

    it('dispara a cobrança manual pela parcela', () => {
      TestBed.inject(CobrancasService).dispararManual('p1').subscribe();
      conferir('POST', '/cobrancas/p1/disparar');
    });

    it('consulta o status do WhatsApp', () => {
      TestBed.inject(CobrancasService).statusWhatsApp().subscribe();
      conferir('GET', '/whatsapp/status');
    });

    it('desconecta o WhatsApp', () => {
      TestBed.inject(CobrancasService).desconectarWhatsApp().subscribe();
      conferir('POST', '/whatsapp/desconectar');
    });
  });

  describe('ConfiguracoesService', () => {
    it('lê as configurações', () => {
      TestBed.inject(ConfiguracoesService).obter().subscribe();
      conferir('GET', '/configuracoes');
    });

    it('salva com PATCH, mandando só o que mudou', () => {
      TestBed.inject(ConfiguracoesService).salvar({ resumo_ativo: false }).subscribe();
      const req = conferir('PATCH', '/configuracoes');
      expect(req.request.body).toEqual({ resumo_ativo: false });
    });

    it('lista os dias com resumo', () => {
      TestBed.inject(ConfiguracoesService).diasDoResumo().subscribe();
      conferir('GET', '/relatorios/resumo/dias', []);
    });

    it('pede o PDF do resumo como arquivo, não como texto', () => {
      TestBed.inject(ConfiguracoesService).resumoEmPdf('2026-09-26').subscribe();
      const req = http.expectOne((r) => r.url === `${API_URL}/relatorios/resumo/pdf`);
      expect(req.request.responseType).toBe('blob');
      req.flush(new Blob());
    });
  });

  describe('DashboardService', () => {
    it('carrega o painel', () => {
      TestBed.inject(DashboardService).carregar().subscribe();
      conferir('GET', '/relatorios/dashboard');
    });

    it('exporta o PDF com o período escolhido', () => {
      const s = TestBed.inject(DashboardService);
      s.exportarPdf('2026-09-01', '2026-09-26').subscribe();
      const req = http.expectOne(`${API_URL}/relatorios/pdf?desde=2026-09-01&ate=2026-09-26`);
      expect(req.request.responseType).toBe('blob');
      req.flush(new Blob());
    });

    it('sem período escolhido, pede o relatório inteiro', () => {
      TestBed.inject(DashboardService).exportarPdf().subscribe();
      http.expectOne(`${API_URL}/relatorios/pdf`).flush(new Blob());
    });
  });

  describe('RankingService', () => {
    it('pede os últimos doze meses por padrão', () => {
      TestBed.inject(RankingService).carregar().subscribe();
      conferir('GET', '/relatorios/ranking?meses=12');
    });

    it('aceita outro período quando pedido', () => {
      TestBed.inject(RankingService).carregar(3).subscribe();
      conferir('GET', '/relatorios/ranking?meses=3');
    });
  });

  describe('TemplatesService', () => {
    it('lista as mensagens', () => {
      TestBed.inject(TemplatesService).listar().subscribe();
      conferir('GET', '/templates', []);
    });

    it('edita a mensagem por PATCH', () => {
      TestBed.inject(TemplatesService).editar('t1', { corpo: 'Olá' }).subscribe();
      conferir('PATCH', '/templates/t1');
    });
  });

  describe('AssinaturaService', () => {
    it('guarda a situação depois de carregar', () => {
      const s = TestBed.inject(AssinaturaService);
      s.carregar().subscribe();
      conferir('GET', '/assinatura', { situacao: 'ativa', dias_restantes: 30 });
      expect(s.atual()?.situacao).toBe('ativa');
    });

    it('bloqueia só quando a assinatura está vencida', () => {
      const s = TestBed.inject(AssinaturaService);

      s.carregar().subscribe();
      conferir('GET', '/assinatura', { situacao: 'vencida', dias_restantes: 0 });
      expect(s.bloqueada()).toBeTrue();

      s.carregar().subscribe();
      conferir('GET', '/assinatura', { situacao: 'isenta', dias_restantes: 0 });
      expect(s.bloqueada()).toBeFalse();
    });

    it('avisa que o teste está acabando a cinco dias do fim', () => {
      const s = TestBed.inject(AssinaturaService);

      s.carregar().subscribe();
      conferir('GET', '/assinatura', { situacao: 'em_teste', dias_restantes: 5 });
      expect(s.acabando()).toBe(5);

      s.carregar().subscribe();
      conferir('GET', '/assinatura', { situacao: 'em_teste', dias_restantes: 6 });
      expect(s.acabando()).toBe(0);

      // Assinatura paga não é "acabando", por mais perto do fim que esteja.
      s.carregar().subscribe();
      conferir('GET', '/assinatura', { situacao: 'ativa', dias_restantes: 1 });
      expect(s.acabando()).toBe(0);
    });

    it('manda o comprovante como arquivo', () => {
      const arquivo = new File(['x'], 'comprovante.png', { type: 'image/png' });
      TestBed.inject(AssinaturaService).enviarComprovante(49.9, arquivo).subscribe();
      const req = http.expectOne((r) => r.method === 'POST' && r.url.endsWith('/assinatura/comprovante'));
      expect(req.request.body instanceof FormData).toBeTrue();
      req.flush({});
    });

    it('aprova e recusa comprovantes por caminhos diferentes', () => {
      const s = TestBed.inject(AssinaturaService);
      s.aprovar('c1').subscribe();
      conferir('POST', '/admin/comprovantes/c1/aprovar');

      s.recusar('c2', 'ilegível').subscribe();
      const req = conferir('POST', '/admin/comprovantes/c2/recusar');
      expect(JSON.stringify(req.request.body)).toContain('ilegível');
    });
  });

  describe('AuthService', () => {
    it('guarda e devolve o crachá', () => {
      const auth = TestBed.inject(AuthService);
      expect(auth.getToken()).toBeNull();

      auth.salvarToken('abc123');
      expect(auth.getToken()).toBe('abc123');
      expect(auth.logado()).toBeTrue();
    });

    it('apaga tudo ao sair e volta para o login', () => {
      const auth = TestBed.inject(AuthService);
      const router = TestBed.inject(Router);
      spyOn(router, 'navigate');

      auth.salvarToken('abc123');
      auth.sair();

      expect(auth.getToken()).toBeNull();
      expect(auth.logado()).toBeFalse();
      expect(auth.administrador()).toBeFalse();
      expect(auth.vendedor()).toBeNull();
      expect(router.navigate).toHaveBeenCalledWith(['/login']);
    });

    it('guarda quem está logado e se é da administração', () => {
      const auth = TestBed.inject(AuthService);
      auth.me().subscribe();
      conferir('GET', '/auth/me', { nome: 'Pamela Baron', administrador: true });

      expect(auth.vendedor()?.nome).toBe('Pamela Baron');
      expect(auth.administrador()).toBeTrue();
    });

    it('monta as iniciais com o primeiro e o último nome', () => {
      const auth = TestBed.inject(AuthService);

      auth.me().subscribe();
      conferir('GET', '/auth/me', { nome: 'Pamela Baron' });
      expect(auth.iniciais()).toBe('PB');

      auth.me().subscribe();
      conferir('GET', '/auth/me', { nome: 'Rosangela dos Santos Ferreira' });
      expect(auth.iniciais()).toBe('RF');

      auth.me().subscribe();
      conferir('GET', '/auth/me', { nome: 'Madonna' });
      expect(auth.iniciais()).toBe('M');

      auth.me().subscribe();
      conferir('GET', '/auth/me', { nome: '   ' });
      expect(auth.iniciais()).toBe('');
    });
  });
});
