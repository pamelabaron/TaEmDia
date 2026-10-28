// Configuração dos testes do frontend.
//
// O navegador roda sem tela (headless) para funcionar dentro de container e
// no CI, onde não existe janela para abrir.
//
// A meta de cobertura é exigência do playbook do portfólio: 25% no frontend
// (o backend tem meta própria, de 75%, conferida pelo pytest). Está aqui, e
// não num documento, porque meta que ninguém mede não é meta: abaixo disso o
// comando falha e o CI reprova o envio.

module.exports = function (config) {
  config.set({
    basePath: '',
    frameworks: ['jasmine', '@angular-devkit/build-angular'],
    plugins: [
      require('karma-jasmine'),
      require('karma-chrome-launcher'),
      require('karma-jasmine-html-reporter'),
      require('karma-coverage'),
      require('@angular-devkit/build-angular/plugins/karma'),
    ],
    client: {
      jasmine: {},
      clearContext: false,
    },
    jasmineHtmlReporter: { suppressAll: true },
    coverageReporter: {
      dir: require('path').join(__dirname, './coverage'),
      subdir: '.',
      reporters: [
        { type: 'html' },
        { type: 'text-summary' },
        { type: 'lcovonly' },
      ],
      check: {
        global: {
          statements: 25,
          lines: 25,
          branches: 25,
          functions: 25,
        },
      },
    },
    reporters: ['progress', 'kjhtml'],
    browsers: ['ChromeHeadless'],
    customLaunchers: {
      // Dentro do container o Chrome não tem permissão para a própria caixa
      // de areia. Desligar é seguro aqui: o que roda é o nosso próprio código.
      ChromeHeadlessCI: {
        base: 'ChromeHeadless',
        flags: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
      },
    },
    restartOnFileChange: true,
  });
};
