/**
 * O servidor grava as datas em UTC e as devolve sem indicar o fuso
 * ("2026-09-13T20:20:57"). Lida assim, o navegador supõe horário local e a
 * tela mostra a hora três horas adiantada no Brasil. Aqui a data é marcada
 * como UTC antes de converter para o horário de quem está vendo.
 */
export function dataHoraLocal(iso: string): string {
  const semFuso = !/[zZ]$|[+-]\d{2}:?\d{2}$/.test(iso);
  const dt = new Date(semFuso ? iso + 'Z' : iso);
  return (
    dt.toLocaleDateString('pt-BR') +
    ', ' +
    dt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  );
}
