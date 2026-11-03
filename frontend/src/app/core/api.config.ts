import { environment } from '../../environments/environment';

/** Endereço base da API. Em produção é /api, servido pelo mesmo domínio. */
export const API_URL = environment.apiUrl;

/** Onde começa o login do Google. Fica fora do /api por causa do cadastro lá. */
export const LOGIN_URL = environment.loginUrl;
