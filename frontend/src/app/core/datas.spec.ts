import { dataHoraLocal } from './datas';

/**
 * O servidor grava em UTC e devolve sem dizer o fuso. Lido cru, o navegador
 * supõe horário local e a tela mostra a hora adiantada. Já aconteceu: um
 * pagamento das 17h aparecia como 20h.
 */
describe('dataHoraLocal', () => {
  it('trata data sem fuso como UTC e converte para o horário de quem vê', () => {
    const esperado = new Date('2026-09-13T20:20:57Z');
    const texto = dataHoraLocal('2026-09-13T20:20:57');

    expect(texto).toContain(esperado.toLocaleDateString('pt-BR'));
    expect(texto).toContain(
      esperado.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    );
  });

  it('não converte de novo quando o fuso já veio escrito', () => {
    // As duas formas descrevem o mesmo instante: o resultado tem de ser igual.
    expect(dataHoraLocal('2026-09-13T20:20:57Z')).toBe(dataHoraLocal('2026-09-13T20:20:57'));
  });

  it('respeita o deslocamento quando ele vem no texto', () => {
    // 17h em Brasília é o mesmo instante que 20h em UTC.
    expect(dataHoraLocal('2026-09-13T17:20:57-03:00')).toBe(dataHoraLocal('2026-09-13T20:20:57Z'));
  });

  it('mostra data e hora separadas por vírgula', () => {
    expect(dataHoraLocal('2026-09-13T20:20:57')).toMatch(/^\d{2}\/\d{2}\/\d{4}, \d{2}:\d{2}$/);
  });
});
