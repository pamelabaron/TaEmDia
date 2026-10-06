/**
 * Faz a cobertura contar o site inteiro, não só o que já tem teste.
 *
 * Por que este arquivo existe: o Karma só mede o que entra na compilação, e
 * só entra o que algum teste importa. Sem isto, a primeira medição deu 72% e
 * o número era falso: o total eram 9 arquivos, os únicos que os testes
 * encostavam. Os outros 26 ficavam de fora da conta, como se não existissem.
 *
 * Meta que mede só a parte boa não é meta. Importando tudo, o denominador
 * passa a ser o site inteiro, e a porcentagem diz o que promete dizer.
 *
 * Não há teste aqui de propósito: os testes de verdade estão ao lado de cada
 * arquivo. Este só garante que ninguém suma da conta.
 */

import './app.component';
import './app.config';
import './app.routes';

import './core/api.config';
import './core/assinatura-necessaria.dialog';
import './core/assinatura.service';
import './core/auth.guard';
import './core/auth.interceptor';
import './core/auth.service';
import './core/clientes.service';
import './core/cobrancas.service';
import './core/configuracoes.service';
import './core/dashboard.service';
import './core/datas';
import './core/erros';
import './core/ranking.service';
import './core/regras-cliente';
import './core/templates.service';
import './core/vendas.service';

import './pages/assinaturas/assinaturas.component';
import './pages/callback/callback.component';
import './pages/cliente-perfil/cliente-perfil.component';
import './pages/clientes/clientes.component';
import './pages/cobrancas/cobrancas.component';
import './pages/configuracoes/cobranca.component';
import './pages/configuracoes/minha-assinatura.component';
import './pages/configuracoes/pagina-assinatura.component';
import './pages/configuracoes/resumo.component';
import './pages/configuracoes/whatsapp.component';
import './pages/dashboard/dashboard.component';
import './pages/login/login.component';
import './pages/ranking/ranking.component';
import './pages/templates/templates.component';

describe('Cobertura', () => {
  it('mede o site inteiro, e não só os arquivos que já têm teste', () => {
    // A verificação real é o próprio relatório de cobertura: se algum arquivo
    // novo não for importado aqui, ele fica fora da conta e a meta vira
    // enfeite. O teste de backend tests/test_cobertura_frontend.py confere
    // que esta lista continua completa.
    expect(true).toBeTrue();
  });
});
