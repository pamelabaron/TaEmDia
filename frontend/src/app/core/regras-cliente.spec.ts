import {
  CODIGO_PAIS_PADRAO,
  DDDS_VALIDOS,
  conferirCpf,
  conferirTelefone,
  cpfValido,
  formatarCpf,
  formatarTelefone,
  soDigitos,
} from './regras-cliente';

/**
 * Espelho dos testes de backend/tests/test_regras_cliente.py.
 *
 * As duas cópias existem porque as duas camadas existem: o servidor decide e
 * a tela avisa antes. Se um dia os resultados divergirem, é aqui que aparece.
 */

describe('Telefone (RN-C01)', () => {
  const esperado = '5547999990000';

  [
    '47999990000',
    '(47) 99999-0000',
    '47 99999-0000',
    '  47999990000  ',
    '5547999990000',
    '+55 (47) 99999-0000',
    '55 47 99999 0000',
  ].forEach((digitado) => {
    it(`aceita "${digitado}" e guarda sempre igual`, () => {
      const r = conferirTelefone(digitado);
      expect(r.ok).toBeTrue();
      expect(r.ok && r.valor).toBe(esperado);
    });
  });

  it('aceita telefone fixo de oito dígitos', () => {
    const r = conferirTelefone('47 3333-0000');
    expect(r.ok && r.valor).toBe('554733330000');
  });

  it('recusa número sem DDD e diz o que falta', () => {
    const r = conferirTelefone('999990000');
    expect(r.ok).toBeFalse();
    expect(!r.ok && r.erro).toContain('DDD');
  });

  ['10', '20', '23', '30', '40', '50', '60', '70', '80', '90'].forEach((ddd) => {
    it(`recusa o DDD ${ddd}, que não existe`, () => {
      const r = conferirTelefone(`${ddd}999990000`);
      expect(r.ok).toBeFalse();
      expect(!r.ok && r.erro).toContain('DDD');
    });
  });

  it('tem os 67 DDDs do país, igual ao backend', () => {
    expect(DDDS_VALIDOS.size).toBe(67);
    ['11', '47', '48', '61', '71', '85', '92', '99'].forEach((ddd) => {
      expect(DDDS_VALIDOS.has(ddd)).toBeTrue();
    });
  });

  it('não confunde o DDD 55 com o código do Brasil', () => {
    const r = conferirTelefone('55999990000');
    expect(r.ok && r.valor).toBe('5555999990000');
  });

  [
    ['4799999', 'curto demais'],
    ['479999900001234', 'longo demais'],
    ['', 'vazio'],
    ['   ', 'só espaço'],
    ['abcdefghijk', 'sem nenhum dígito'],
  ].forEach(([valor, motivo]) => {
    it(`recusa "${valor}" (${motivo})`, () => {
      expect(conferirTelefone(valor).ok).toBeFalse();
    });
  });

  it('recusa nove dígitos que não começam com 9', () => {
    expect(conferirTelefone('47 89999-0000').ok).toBeFalse();
  });

  it('aceita outro país quando informado', () => {
    const r = conferirTelefone('351 912 345 678', '351');
    expect(r.ok && r.valor).toBe('351912345678');
  });

  it('recusa código de país que não é número', () => {
    const r = conferirTelefone('47999990000', 'abc');
    expect(r.ok).toBeFalse();
    expect(!r.ok && r.erro).toContain('país');
  });

  it('usa o 55 quando o campo do país vem em branco', () => {
    expect(CODIGO_PAIS_PADRAO).toBe('55');
    const r = conferirTelefone('47999990000', '');
    expect(r.ok && r.valor).toBe(esperado);
  });
});

describe('Telefone na tela', () => {
  it('mostra celular como 55 (47) 99999-0000', () => {
    expect(formatarTelefone('5547999990000')).toBe('55 (47) 99999-0000');
  });

  it('mostra fixo como 55 (47) 3333-0000', () => {
    expect(formatarTelefone('554733330000')).toBe('55 (47) 3333-0000');
  });

  it('não inventa formato brasileiro para número de fora', () => {
    expect(formatarTelefone('351912345678')).toBe('+351912345678');
  });

  it('devolve o valor como veio quando não dá para formatar', () => {
    expect(formatarTelefone('')).toBe('');
    expect(formatarTelefone(null)).toBe('');
    expect(formatarTelefone('123')).toBe('123');
  });
});

describe('CPF (RN-C02)', () => {
  it('guarda só os dígitos', () => {
    const r = conferirCpf('529.982.247-25');
    expect(r.ok && r.valor).toBe('52998224725');
  });

  [null, undefined, '', '   '].forEach((vazio) => {
    it(`aceita campo vazio (${JSON.stringify(vazio)}), porque o CPF é opcional`, () => {
      const r = conferirCpf(vazio);
      expect(r.ok).toBeTrue();
      expect(r.ok && r.valor).toBe('');
    });
  });

  [
    ['5299822472', 10],
    ['529982247251', 12],
    ['529', 3],
  ].forEach(([cpf, quantidade]) => {
    it(`recusa CPF com ${quantidade} dígitos`, () => {
      const r = conferirCpf(cpf as string);
      expect(r.ok).toBeFalse();
      expect(!r.ok && r.erro).toContain('11');
    });
  });

  ['00000000000', '11111111111', '55555555555', '99999999999'].forEach((repetido) => {
    it(`recusa "${repetido}", que passa no tamanho mas não é CPF`, () => {
      expect(conferirCpf(repetido).ok).toBeFalse();
    });
  });

  ['52998224726', '52998224715', '11144477736', '12345678900'].forEach((errado) => {
    it(`recusa "${errado}", com dígito verificador errado`, () => {
      const r = conferirCpf(errado);
      expect(r.ok).toBeFalse();
      expect(!r.ok && r.erro).toContain('CPF');
    });
  });

  ['52998224725', '11144477735', '12345678909'].forEach((valido) => {
    it(`aceita o CPF válido ${valido}`, () => {
      expect(conferirCpf(valido).ok).toBeTrue();
    });
  });

  it('recusa letra no meio', () => {
    expect(conferirCpf('529.98a.247-25').ok).toBeFalse();
  });

  it('cpfValido recusa o que não é só dígito', () => {
    expect(cpfValido('5299822472a')).toBeFalse();
    expect(cpfValido('529')).toBeFalse();
    expect(cpfValido('52998224725')).toBeTrue();
  });

  it('mostra o CPF pontuado na tela', () => {
    expect(formatarCpf('52998224725')).toBe('529.982.247-25');
    expect(formatarCpf('529')).toBe('529');
    expect(formatarCpf(null)).toBe('');
  });
});

describe('soDigitos', () => {
  it('joga fora tudo que não é número', () => {
    expect(soDigitos('+55 (47) 99999-0000')).toBe('5547999990000');
    expect(soDigitos(null)).toBe('');
    expect(soDigitos('abc')).toBe('');
  });
});
