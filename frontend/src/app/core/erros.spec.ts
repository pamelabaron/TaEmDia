import { bloqueadoPorAssinatura } from './erros';

/**
 * A trava da assinatura é a regra de negócio mais importante do frontend: é o
 * que separa "pode usar" de "precisa assinar". Ela já causou um problema de
 * verdade, quando o aviso genérico da tela ("Erro ao cadastrar cliente")
 * cobria o diálogo de assinatura e a pessoa não entendia por que foi barrada.
 */
describe('bloqueadoPorAssinatura', () => {
  it('reconhece a recusa por assinatura (402)', () => {
    expect(bloqueadoPorAssinatura({ status: 402 })).toBeTrue();
  });

  [400, 401, 403, 404, 409, 422, 500].forEach((status) => {
    it(`não confunde o erro ${status} com falta de assinatura`, () => {
      expect(bloqueadoPorAssinatura({ status })).toBeFalse();
    });
  });

  it('aguenta erro sem formato conhecido sem quebrar a tela', () => {
    expect(bloqueadoPorAssinatura(null)).toBeFalse();
    expect(bloqueadoPorAssinatura(undefined)).toBeFalse();
    expect(bloqueadoPorAssinatura('deu ruim')).toBeFalse();
    expect(bloqueadoPorAssinatura({})).toBeFalse();
    expect(bloqueadoPorAssinatura(new Error('falhou'))).toBeFalse();
  });

  it('não aceita o 402 escrito como texto', () => {
    // Comparação estrita de propósito: status vem como número da resposta.
    expect(bloqueadoPorAssinatura({ status: '402' })).toBeFalse();
  });
});
