import { Type } from '@angular/core';

import { AssinaturasComponent } from './pages/assinaturas/assinaturas.component';
import { ClientePerfilComponent } from './pages/cliente-perfil/cliente-perfil.component';
import { ClientesComponent } from './pages/clientes/clientes.component';
import { CobrancasComponent } from './pages/cobrancas/cobrancas.component';
import { ConfigCobrancaComponent } from './pages/configuracoes/cobranca.component';
import { ConfigResumoComponent } from './pages/configuracoes/resumo.component';
import { ConfigWhatsappComponent } from './pages/configuracoes/whatsapp.component';
import { MinhaAssinaturaComponent } from './pages/configuracoes/minha-assinatura.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { TemplatesComponent } from './pages/templates/templates.component';

/**
 * As dez telas internas e o que cada uma pede ao abrir.
 *
 * Existe para que os testes que montam telas (contraste, estados) usem a mesma
 * definição. Antes isso vivia duplicado em dois arquivos de teste, e o
 * desencontro entre as duas cópias era questão de tempo.
 *
 * Não é código do sistema: nada aqui vai para o navegador de quem usa. Por
 * isso está fora da conta da cobertura, registrado em
 * backend/tests/test_cobertura_frontend.py.
 */

/** Uma resposta que o teste dá no lugar da API: o caminho e o corpo. */
export type Resposta = [caminho: string, corpo: unknown];

export interface TelaDeTeste {
  /** Como a tela se chama para quem usa o sistema. */
  nome: string;
  componente: Type<unknown>;
  /** Parâmetros de rota, quando a tela depende de um (o perfil do cliente). */
  rota?: Record<string, string>;
  /** O que a API responde quando há dados. */
  cheia: Resposta[];
  /** O que a API responde quando a conta é nova e ainda não há nada. */
  vazia: Resposta[];
  /** Tela de formulário não tem estado vazio: ela mostra os campos. */
  eFormulario?: boolean;
}

const CLIENTE = {
  id: '1',
  nome: 'Rosangela Ferreira',
  whatsapp_numero: '5547999990000',
  whatsapp_formatado: '55 (47) 99999-0000',
  cpf: null,
  endereco: null,
  envio_auto_ativo: true,
  interacao_habilitada: true,
  ativo: true,
  criado_em: '2026-09-01T10:00:00',
};

const CONFIGURACAO = {
  id: '1',
  dias_antecedencia_lembrete: 3,
  horario_resumo: '20:00',
  resumo_ativo: true,
  envio_auto_global: true,
  canal_resumo: 'ambos',
  email_resumo: 'voce@exemplo.com',
  whatsapp_resumo: '5547999990000',
};

export const TELAS: TelaDeTeste[] = [
  {
    nome: 'Painel',
    componente: DashboardComponent,
    cheia: [['/relatorios/dashboard', {
      total_a_receber: 4820.5, recebido_no_mes: 1270, em_atraso: 640.9,
      clientes_inadimplentes: 2,
      recebimentos_mensais: [{ mes: '2026-08', total: 980 }, { mes: '2026-09', total: 1270 }],
      clientes_em_atraso: [{ id: '1', nome: 'Rosangela Ferreira', valor_atrasado: 320.4 }],
    }]],
    vazia: [['/relatorios/dashboard', {
      total_a_receber: 0, recebido_no_mes: 0, em_atraso: 0,
      clientes_inadimplentes: 0, recebimentos_mensais: [], clientes_em_atraso: [],
    }]],
  },
  {
    nome: 'Clientes',
    componente: ClientesComponent,
    cheia: [['/clientes', [CLIENTE]]],
    vazia: [['/clientes', []]],
  },
  {
    nome: 'Perfil do cliente',
    componente: ClientePerfilComponent,
    rota: { id: '1' },
    cheia: [['/clientes/1/perfil', {
      ...CLIENTE, cpf_formatado: '', saldo_devedor: 300,
      vendas: [{
        id: 'v1', cliente_id: '1', valor_total: 300, num_parcelas: 3,
        data_primeira_parcela: '2026-10-05', status: 'ativa',
        criado_em: '2026-09-01T10:00:00',
        parcelas: [{
          id: 'p1', numero_parcela: 1, valor: 100,
          data_vencimento: '2026-10-05', data_pagamento: null, status: 'pendente',
        }],
      }],
    }]],
    vazia: [['/clientes/1/perfil', {
      ...CLIENTE, cpf_formatado: '', saldo_devedor: 0, vendas: [],
    }]],
  },
  {
    nome: 'Cobranças',
    componente: CobrancasComponent,
    cheia: [
      ['/cobrancas', [{
        id: '1', cliente_id: '1', cliente_nome: 'Rosangela Ferreira', parcela_id: '1',
        tipo: 'lembrete', conteudo: 'Olá! Sua parcela vence amanhã.',
        status: 'enviado', criado_em: '2026-09-25T09:00:00',
      }]],
      ['/whatsapp/status', {
        conectado: true, numero: '5547999990000', qrcode: null,
        detalhe: '', modo_simulador: true,
      }],
    ],
    vazia: [
      ['/cobrancas', []],
      ['/whatsapp/status', {
        conectado: false, numero: null, qrcode: null,
        detalhe: '', modo_simulador: true,
      }],
    ],
  },
  {
    nome: 'Mensagens',
    componente: TemplatesComponent,
    cheia: [['/templates', [{
      id: '1', tipo: 'lembrete', titulo: 'Lembrete de vencimento',
      corpo: 'Olá {nome}, sua parcela vence em {dias} dias.',
      is_padrao: true, ativo: true,
    }]]],
    vazia: [['/templates', []]],
  },
  {
    nome: 'WhatsApp',
    componente: ConfigWhatsappComponent,
    cheia: [['/whatsapp/status', {
      conectado: true, numero: '5547999990000', qrcode: null,
      detalhe: '', modo_simulador: false,
    }]],
    vazia: [['/whatsapp/status', {
      conectado: false, numero: null, qrcode: null,
      detalhe: '', modo_simulador: false,
    }]],
  },
  {
    nome: 'Cobrança automática',
    componente: ConfigCobrancaComponent,
    eFormulario: true,
    cheia: [['/configuracoes', { ...CONFIGURACAO }]],
    vazia: [['/configuracoes', { ...CONFIGURACAO }]],
  },
  {
    nome: 'Resumo diário',
    componente: ConfigResumoComponent,
    cheia: [
      ['/configuracoes', { ...CONFIGURACAO }],
      ['/relatorios/resumo/dias', ['2026-10-14', '2026-10-13']],
      ['/relatorios/resumo', {
        dia: '2026-10-14', houve_atividade: true,
        cobrancas_enviadas: 4, cobrancas_falharam: 1, pagamentos: 2,
        valor_recebido: 310.5, sem_resposta: 2,
        respostas: { '1_ja_paguei': 1, '2_pago_hoje': 1, '3_nao_consigo': 0 },
        rotulos: {
          '1_ja_paguei': 'Já paguei', '2_pago_hoje': 'Vou pagar hoje',
          '3_nao_consigo': 'Não consigo pagar',
        },
      }],
    ],
    vazia: [
      ['/configuracoes', { ...CONFIGURACAO }],
      ['/relatorios/resumo/dias', ['2026-10-14']],
      ['/relatorios/resumo', {
        dia: '2026-10-14', houve_atividade: false,
        cobrancas_enviadas: 0, cobrancas_falharam: 0, pagamentos: 0,
        valor_recebido: 0, sem_resposta: 0, respostas: {}, rotulos: {},
      }],
    ],
  },
  {
    nome: 'Minha assinatura',
    componente: MinhaAssinaturaComponent,
    cheia: [['/assinatura', {
      situacao: 'ativa', valido_ate: '2026-11-14', dias_restantes: 30,
      tem_pendente: false, valor_mensal: 49.9,
      pix_chave: 'exemplo@taemdia', pix_nome: 'TáEmDia',
      historico: [{
        id: 'p1', valor: 49.9, arquivo_nome: 'comprovante.png',
        situacao: 'aprovado', enviado_em: '2026-10-01T10:00:00',
        avaliado_em: '2026-10-01T12:00:00', observacao: null,
      }],
    }]],
    vazia: [['/assinatura', {
      situacao: 'em_teste', valido_ate: '2026-10-21', dias_restantes: 7,
      tem_pendente: false, valor_mensal: 49.9,
      pix_chave: 'exemplo@taemdia', pix_nome: 'TáEmDia', historico: [],
    }]],
  },
  {
    nome: 'Comprovantes',
    componente: AssinaturasComponent,
    cheia: [['/admin/comprovantes', [{
      id: 'p1', valor: 49.9, arquivo_nome: 'comprovante.png',
      situacao: 'pendente', enviado_em: '2026-10-01T10:00:00',
      avaliado_em: null, observacao: null,
      vendedor_id: 'v1', vendedor_nome: 'Rosangela Ferreira',
      vendedor_email: 'rosangela@exemplo.com',
    }]]],
    vazia: [['/admin/comprovantes', []]],
  },
];
