/** Produção: o Nginx serve o site e a API no mesmo endereço.
 *
 * A API fica sob /api para não colidir com as telas do site: havia rotas com o
 * mesmo nome nos dois lados (/clientes, /cobrancas, /configuracoes), e atualizar
 * a página devolvia JSON no lugar do sistema.
 *
 * O login do Google é a exceção e continua na raiz, porque o endereço de
 * retorno já está cadastrado no Google Cloud.
 */
export const environment = {
  apiUrl: '/api',
  loginUrl: '/auth/google/login',
};
