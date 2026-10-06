/**
 * Regras de CPF e telefone do cliente (RN-C01 e RN-C02).
 *
 * Cópia em TypeScript das regras que vivem em
 * backend/app/modules/clientes/regras.py. A repetição é proposital: a API
 * decide, esta cópia só avisa na hora, enquanto a pessoa digita, em vez de
 * fazer a viagem até o servidor para descobrir que faltou um dígito.
 *
 * Quem manda é o servidor. Se as duas discordarem, vale a resposta da API.
 */

/** Código do país que o formulário já traz preenchido. */
export const CODIGO_PAIS_PADRAO = '55';

/**
 * Os 67 DDDs em uso no Brasil. A lista existe porque a faixa de 11 a 99 tem
 * buracos (não existe DDD 20, 30, 40...), e erro de digitação cai neles.
 */
export const DDDS_VALIDOS: ReadonlySet<string> = new Set([
  '11', '12', '13', '14', '15', '16', '17', '18', '19',
  '21', '22', '24', '27', '28',
  '31', '32', '33', '34', '35', '37', '38',
  '41', '42', '43', '44', '45', '46', '47', '48', '49',
  '51', '53', '54', '55',
  '61', '62', '63', '64', '65', '66', '67', '68', '69',
  '71', '73', '74', '75', '77', '79',
  '81', '82', '83', '84', '85', '86', '87', '88', '89',
  '91', '92', '93', '94', '95', '96', '97', '98', '99',
]);

/** Oito é telefone fixo, nove é celular. Os dois valem para o WhatsApp. */
const TAMANHOS_BRASIL = [8, 9];
const MINIMO_INTERNACIONAL = 8;
const MAXIMO_INTERNACIONAL = 15;
const DIGITOS_DO_CPF = 11;

/** Resultado de uma conferência: ou o valor pronto, ou o motivo da recusa. */
export type Conferencia =
  | { ok: true; valor: string }
  | { ok: false; erro: string };

export function soDigitos(texto: string | null | undefined): string {
  return (texto ?? '').replace(/\D/g, '');
}

function limparCodigoPais(codigoPais: string | null | undefined): Conferencia {
  const bruto = (codigoPais ?? '').trim();
  if (!bruto) return { ok: true, valor: CODIGO_PAIS_PADRAO };

  const pais = soDigitos(bruto);
  if (!pais || pais.length > 3) {
    return { ok: false, erro: 'Código do país inválido. Use de 1 a 3 dígitos, como 55.' };
  }
  return { ok: true, valor: pais };
}

/**
 * Tira o código do país quando a pessoa o digitou junto do número.
 *
 * O corte olha o que sobra, não só o começo: sem isso o DDD 55 (Rio Grande do
 * Sul) seria confundido com o código do Brasil e o número perderia o DDD.
 */
function tirarCodigoRepetido(digitos: string, pais: string): string {
  if (!digitos.startsWith(pais)) return digitos;

  const resto = digitos.slice(pais.length);
  const cabeComoNacional =
    pais === CODIGO_PAIS_PADRAO
      ? TAMANHOS_BRASIL.includes(resto.length - 2)
      : resto.length >= 6;

  return cabeComoNacional ? resto : digitos;
}

/**
 * Deixa o número pronto para o WhatsApp: código do país, DDD e número.
 *
 * O WhatsApp exige o código do país. Guardar sem ele faz a cobrança sair do
 * sistema e não chegar em ninguém, sem erro nenhum aparecer no caminho.
 */
export function conferirTelefone(
  numero: string | null | undefined,
  codigoPais: string = CODIGO_PAIS_PADRAO,
): Conferencia {
  const pais = limparCodigoPais(codigoPais);
  if (!pais.ok) return pais;

  const digitos = soDigitos(numero);
  if (!digitos) {
    return { ok: false, erro: 'Informe o número do WhatsApp com DDD.' };
  }

  const nacional = tirarCodigoRepetido(digitos, pais.valor);

  if (pais.valor !== CODIGO_PAIS_PADRAO) {
    const completo = pais.valor + nacional;
    if (completo.length < MINIMO_INTERNACIONAL || completo.length > MAXIMO_INTERNACIONAL) {
      return {
        ok: false,
        erro: `Número inválido para o país ${pais.valor}. `
          + `Use de ${MINIMO_INTERNACIONAL} a ${MAXIMO_INTERNACIONAL} dígitos.`,
      };
    }
    return { ok: true, valor: completo };
  }

  if (!TAMANHOS_BRASIL.includes(nacional.length - 2)) {
    return {
      ok: false,
      erro: nacional.length < 10
        ? 'Informe o número com DDD. Exemplo: 47 99999-0000.'
        : 'Número muito longo. Use DDD e o número, como 47 99999-0000.',
    };
  }

  const ddd = nacional.slice(0, 2);
  const resto = nacional.slice(2);

  if (!DDDS_VALIDOS.has(ddd)) {
    return { ok: false, erro: `DDD ${ddd} não existe. Confira o número.` };
  }
  if (resto.length === 9 && !resto.startsWith('9')) {
    return {
      ok: false,
      erro: 'Celular de nove dígitos começa com 9. Confira se sobrou um dígito.',
    };
  }

  return { ok: true, valor: pais.valor + nacional };
}

/**
 * Como o número aparece na tela: "55 (47) 99999-0000".
 *
 * Enfeite, não regra: recebe qualquer coisa e devolve algo legível, porque
 * dado antigo não pode derrubar a listagem de clientes.
 */
export function formatarTelefone(guardado: string | null | undefined): string {
  const digitos = soDigitos(guardado);
  if (!digitos) return guardado ?? '';

  if (digitos.startsWith(CODIGO_PAIS_PADRAO) && TAMANHOS_BRASIL.includes(digitos.length - 4)) {
    const ddd = digitos.slice(2, 4);
    const resto = digitos.slice(4);
    return `${CODIGO_PAIS_PADRAO} (${ddd}) ${resto.slice(0, -4)}-${resto.slice(-4)}`;
  }

  return digitos.length >= MINIMO_INTERNACIONAL ? `+${digitos}` : (guardado ?? '');
}

/** Um dígito do fim do CPF, pela conta oficial da Receita. */
function digitoVerificador(base: string, pesoInicial: number): string {
  let soma = 0;
  for (let i = 0; i < base.length; i++) {
    soma += Number(base[i]) * (pesoInicial - i);
  }
  const resto = (soma * 10) % 11;
  return resto === 10 ? '0' : String(resto);
}

/**
 * Os dois últimos números conferem com o resto? (RN-C02)
 *
 * É o que separa um CPF de onze algarismos quaisquer. Pega erro de digitação
 * e pega o "111.111.111-11" que as pessoas usam para vencer campo obrigatório.
 */
export function cpfValido(digitos: string): boolean {
  if (digitos.length !== DIGITOS_DO_CPF || !/^\d+$/.test(digitos)) return false;
  if (digitos === digitos[0].repeat(DIGITOS_DO_CPF)) return false;

  const primeiro = digitoVerificador(digitos.slice(0, 9), 10);
  const segundo = digitoVerificador(digitos.slice(0, 10), 11);
  return digitos.slice(9) === primeiro + segundo;
}

/**
 * Confere o CPF. Campo vazio passa: o CPF é opcional no cadastro (RF04).
 */
export function conferirCpf(cpf: string | null | undefined): Conferencia {
  const bruto = (cpf ?? '').trim();
  if (!bruto) return { ok: true, valor: '' };

  const digitos = soDigitos(bruto);
  if (digitos.length !== DIGITOS_DO_CPF) {
    return { ok: false, erro: `O CPF tem ${DIGITOS_DO_CPF} dígitos. Confira o número.` };
  }
  if (!cpfValido(digitos)) {
    return { ok: false, erro: 'CPF inválido. Confira os números digitados.' };
  }
  return { ok: true, valor: digitos };
}

/** CPF na tela: "529.982.247-25". */
export function formatarCpf(guardado: string | null | undefined): string {
  const digitos = soDigitos(guardado);
  if (digitos.length !== DIGITOS_DO_CPF) return guardado ?? '';
  return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-${digitos.slice(9)}`;
}
