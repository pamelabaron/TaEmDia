import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { Type } from '@angular/core';

import { ClientesComponent } from './pages/clientes/clientes.component';
import { CobrancasComponent } from './pages/cobrancas/cobrancas.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { RankingComponent } from './pages/ranking/ranking.component';
import { TemplatesComponent } from './pages/templates/templates.component';
import { ConfigCobrancaComponent } from './pages/configuracoes/cobranca.component';
import { ConfigResumoComponent } from './pages/configuracoes/resumo.component';

/**
 * O tema escuro, conferido por medição e não por olhar.
 *
 * As telas internas exigem sessão, e abrir todas no navegador para olhar uma a
 * uma é caro e não deixa rastro: na próxima mudança de cor, alguém teria de
 * olhar tudo de novo. Aqui cada tela é montada de verdade, com a folha de
 * estilo do projeto carregada, e o contraste de cada texto é calculado.
 *
 * Foi o que pegou, na página de entrada, quatro textos que o tema escuro
 * deixou ilegíveis: o nome da marca, o destaque do título e dois botões.
 */

/** Luminância relativa, pela fórmula da WCAG. */
function luminancia(cor: string): number | null {
  // Aceita as duas escritas: "rgb(20, 15, 26)", que vem do getComputedStyle,
  // e "#4fd98c", que é como os tokens estão escritos na folha de estilo.
  let canais: number[];

  const hex = cor.trim().match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hex) {
    const d = hex[1].length === 3
      ? hex[1].split('').map((c) => c + c).join('')
      : hex[1];
    canais = [0, 2, 4].map((i) => parseInt(d.slice(i, i + 2), 16) / 255);
  } else {
    const partes = cor.match(/[\d.]+/g);
    if (!partes || partes.length < 3) return null;
    canais = partes.slice(0, 3).map((v) => Number(v) / 255);
  }

  const lin = canais.map((x) => (x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4)));
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

function contraste(frente: string, fundo: string): number | null {
  const a = luminancia(frente);
  const b = luminancia(fundo);
  if (a === null || b === null) return null;
  const [alto, baixo] = a > b ? [a, b] : [b, a];
  return (alto + 0.05) / (baixo + 0.05);
}

/**
 * O fundo que de fato aparece atrás do elemento.
 *
 * Sobe pelos pais até achar um fundo opaco o bastante para contar: medir
 * contra o fundo do próprio elemento daria "transparente" quase sempre.
 */
function fundoReal(el: Element): string {
  let atual: Element | null = el;
  while (atual && atual !== document.documentElement) {
    const cor = getComputedStyle(atual).backgroundColor;
    const partes = cor.match(/[\d.]+/g);
    if (partes && (partes.length < 4 || Number(partes[3]) > 0.55)) return cor;
    atual = atual.parentElement;
  }
  return getComputedStyle(document.body).backgroundColor;
}

interface Reprovado {
  texto: string;
  cor: string;
  fundo: string;
  contraste: number;
  minimo: number;
}

function textosComContrasteBaixo(raiz: Element): Reprovado[] {
  const ruins: Reprovado[] = [];

  for (const el of Array.from(raiz.querySelectorAll('*'))) {
    const temTexto = Array.from(el.childNodes).some(
      (n) => n.nodeType === Node.TEXT_NODE && (n.textContent ?? '').trim().length > 1,
    );
    if (!temTexto) continue;

    const estilo = getComputedStyle(el);
    if (estilo.visibility === 'hidden' || estilo.display === 'none') continue;
    if (Number(estilo.opacity) === 0) continue;

    const c = contraste(estilo.color, fundoReal(el));
    if (c === null) continue;

    const px = parseFloat(estilo.fontSize);
    const grande = px >= 24 || (px >= 18.66 && Number(estilo.fontWeight) >= 700);
    const minimo = grande ? 3 : 4.5;

    if (c < minimo) {
      ruins.push({
        texto: (el.textContent ?? '').trim().slice(0, 40),
        cor: estilo.color,
        fundo: fundoReal(el),
        contraste: Math.round(c * 100) / 100,
        minimo,
      });
    }
  }
  return ruins;
}

/** As telas e o que cada uma pede ao abrir, para o teste poder responder. */
const TELAS: { nome: string; componente: Type<unknown>; respostas: [string, unknown][] }[] = [
  {
    nome: 'Clientes',
    componente: ClientesComponent,
    respostas: [['/clientes', [
      { id: '1', nome: 'Rosangela Ferreira', whatsapp_numero: '5547999990000',
        whatsapp_formatado: '55 (47) 99999-0000', cpf: null, endereco: null,
        envio_auto_ativo: true, interacao_habilitada: true, ativo: true,
        criado_em: '2026-09-01T10:00:00' },
    ]]],
  },
  {
    nome: 'Painel',
    componente: DashboardComponent,
    respostas: [['/relatorios/dashboard', {
      total_a_receber: 4820.5, recebido_no_mes: 1270, em_atraso: 640.9,
      clientes_inadimplentes: 2,
      recebimentos_mensais: [{ mes: '2026-08', total: 980 }, { mes: '2026-09', total: 1270 }],
      clientes_em_atraso: [{ id: '1', nome: 'Rosangela Ferreira', valor_atrasado: 320.4 }],
    }]],
  },
  {
    nome: 'Cobranças',
    componente: CobrancasComponent,
    respostas: [
      ['/cobrancas', [
        { id: '1', cliente_id: '1', cliente_nome: 'Rosangela Ferreira', parcela_id: '1',
          tipo: 'lembrete', conteudo: 'Olá! Sua parcela vence amanhã.', status: 'enviado',
          criado_em: '2026-09-25T09:00:00' },
        { id: '2', cliente_id: '1', cliente_nome: 'Rosangela Ferreira', parcela_id: '2',
          tipo: 'manual', conteudo: 'Lembrete manual.', status: 'falhou',
          criado_em: '2026-09-25T10:00:00' },
      ]],
      ['/whatsapp/status', { conectado: true, numero: '5547999990000', detalhe: '', modo_simulador: true }],
    ],
  },
  {
    nome: 'Ranking',
    componente: RankingComponent,
    respostas: [['/relatorios/ranking', {
      bons: 1, regulares: 1, inadimplentes: 1, sem_historico: 1,
      clientes: [
        { id: '1', nome: 'Rosangela Ferreira', classificacao: 'bom',
          percentual_em_dia: 92, media_dias_atraso: 0.4, total_avaliadas: 12 },
        { id: '2', nome: 'Marcelo Antunes', classificacao: 'regular',
          percentual_em_dia: 61, media_dias_atraso: 6.2, total_avaliadas: 8 },
        { id: '3', nome: 'Tereza Albuquerque', classificacao: 'inadimplente',
          percentual_em_dia: 22, media_dias_atraso: 31.5, total_avaliadas: 6 },
        { id: '4', nome: 'Joana Medeiros', classificacao: 'sem_historico',
          percentual_em_dia: 0, media_dias_atraso: 0, total_avaliadas: 0 },
      ],
    }]],
  },
  {
    nome: 'Mensagens',
    componente: TemplatesComponent,
    respostas: [['/templates', [
      { id: '1', tipo: 'lembrete', titulo: 'Lembrete de vencimento',
        corpo: 'Olá {nome}, sua parcela vence em {dias} dias.', is_padrao: true, ativo: true },
    ]]],
  },
  {
    nome: 'Cobrança automática',
    componente: ConfigCobrancaComponent,
    respostas: [['/configuracoes', {
      id: '1', dias_antecedencia_lembrete: 3, horario_resumo: '20:00', resumo_ativo: true,
      envio_auto_global: true, canal_resumo: 'whatsapp', email_resumo: null,
      whatsapp_resumo: null,
    }]],
  },
  {
    nome: 'Resumo diário',
    componente: ConfigResumoComponent,
    respostas: [
      ['/configuracoes', {
        id: '1', dias_antecedencia_lembrete: 3, horario_resumo: '20:00', resumo_ativo: true,
        envio_auto_global: true, canal_resumo: 'ambos', email_resumo: 'voce@exemplo.com',
        whatsapp_resumo: '5547999990000',
      }],
      ['/relatorios/resumo/dias', ['2026-10-06', '2026-10-05']],
      ['/relatorios/resumo', {
        dia: '2026-10-06', houve_atividade: true,
        cobrancas_enviadas: 4, cobrancas_falharam: 1, pagamentos: 2,
        valor_recebido: 310.5, sem_resposta: 2,
        respostas: { '1_ja_paguei': 1, '2_pago_hoje': 1, '3_nao_consigo': 0 },
        rotulos: { '1_ja_paguei': 'Já paguei', '2_pago_hoje': 'Vou pagar hoje',
                   '3_nao_consigo': 'Não consigo pagar' },
      }],
    ],
  },
];

describe('Tema escuro', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        provideNoopAnimations(),
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });

  it('a página tem fundo escuro e texto claro', () => {
    const corpo = getComputedStyle(document.body);
    const lFundo = luminancia(corpo.backgroundColor);
    const lTexto = luminancia(corpo.color);

    expect(lFundo).not.toBeNull();
    expect(lFundo!).toBeLessThan(0.1);
    expect(lTexto!).toBeGreaterThan(0.5);
  });

  it('os estados continuam distinguíveis entre si', () => {
    // Verde pago, laranja atraso, vermelho inadimplente, cinza pendente. Se
    // dois virarem a mesma cor, a leitura de relance do painel acaba. Já
    // aconteceu neste projeto, com "Paga" e "Pendente" ambos verdes.
    const raiz = getComputedStyle(document.documentElement);
    const estados = ['--sucesso', '--alerta', '--perigo', '--neutro']
      .map((nome) => raiz.getPropertyValue(nome).trim());

    expect(new Set(estados).size).toBe(4);
    estados.forEach((cor) => expect(cor).not.toBe(''));
  });

  it('cada cor de estado se lê sobre o fundo da página', () => {
    const raiz = getComputedStyle(document.documentElement);
    const fundo = getComputedStyle(document.body).backgroundColor;

    for (const nome of ['--sucesso', '--alerta', '--perigo', '--neutro', '--texto', '--texto-suave', '--texto-fraco']) {
      const cor = raiz.getPropertyValue(nome).trim();
      const c = contraste(cor, fundo);
      expect(c).withContext(`${nome} (${cor}) sobre ${fundo}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  TELAS.forEach(({ nome, componente, respostas }) => {
    it(`nenhum texto ilegível na tela "${nome}"`, () => {
      const fixture = TestBed.createComponent(componente);
      fixture.detectChanges();

      for (const [caminho, corpo] of respostas) {
        // Compara só o caminho: vários endereços levam parâmetros na ponta
        // ("/cobrancas?periodo=hoje"), e exigir que termine no caminho fazia
        // o pedido cair na resposta genérica, com o formato errado.
        const pedidos = http.match((r) => r.url.split('?')[0].endsWith(caminho));
        pedidos.forEach((p) => p.flush(corpo as object));
      }
      // Qualquer outra chamada que a tela faça ao abrir não interessa aqui.
      // Responde com lista vazia: a maioria espera uma coleção, e um objeto
      // solto rebenta o @for antes de a tela chegar a desenhar.
      http.match(() => true).forEach((p) => p.flush([]));
      fixture.detectChanges();

      const ruins = textosComContrasteBaixo(fixture.nativeElement);
      expect(ruins)
        .withContext(`Textos abaixo do contraste mínimo: ${JSON.stringify(ruins, null, 1)}`)
        .toEqual([]);
    });
  });
});
