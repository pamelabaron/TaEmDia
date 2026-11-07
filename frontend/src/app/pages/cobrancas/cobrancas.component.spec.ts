import { CobrancasComponent } from './cobrancas.component';

/**
 * A tela de Cobranças conhecia duas situações: "Enviada" e, para todo o
 * resto, "Na fila". Quando o reenvio (FE01) passou a descartar a mensagem que
 * deixou de fazer sentido (parcela paga, venda cancelada, dia virado), ela
 * apareceria como "Na fila" para sempre, prometendo um envio que nunca vem.
 *
 * O contraste dos três rótulos é medido em tema-escuro.spec.ts, a partir das
 * mensagens de exemplo em telas.fixtures.ts.
 */
describe('CobrancasComponent: situação da mensagem', () => {
  function rotulo(status: string): string {
    // O rótulo é função pura da situação: não precisa montar a tela.
    return CobrancasComponent.prototype.rotuloStatus.call({}, status);
  }

  it('diz "Enviada" para o que saiu', () => {
    expect(rotulo('enviado')).toBe('Enviada');
  });

  it('diz "Na fila" para o que espera reenvio', () => {
    expect(rotulo('pendente')).toBe('Na fila');
  });

  it('diz "Não enviada" para o que foi descartado, e não "Na fila"', () => {
    expect(rotulo('descartada')).toBe('Não enviada');
  });

  it('situação desconhecida cai em "Na fila", nunca em texto cru', () => {
    expect(rotulo('qualquer-coisa')).toBe('Na fila');
  });
});
