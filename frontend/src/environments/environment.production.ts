/** Produção: o Nginx serve a interface e a API no mesmo endereço.
 *
 * Por isso o endereço da API fica vazio: as chamadas saem relativas e vão para
 * o mesmo domínio que abriu a página. Fixar "localhost:8000" aqui faria o site
 * publicado chamar o computador de quem está visitando. Que foi exatamente o
 * defeito que motivou esta separação.
 */
export const environment = {
  apiUrl: '',
};
