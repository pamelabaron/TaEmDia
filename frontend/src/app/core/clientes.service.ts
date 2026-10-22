import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export interface Cliente {
  id: string;
  nome: string;
  whatsapp_numero: string;
  /** Pronto para a tela: "55 (47) 99999-0000". Vem calculado da API, para
   *  que o site não repita a regra de formatação e as duas não discordem. */
  whatsapp_formatado: string;
  cpf: string | null;
  endereco: string | null;
  envio_auto_ativo: boolean;
  interacao_habilitada: boolean;
  ativo: boolean;
  criado_em: string;
}

export interface ClienteCreate {
  nome: string;
  whatsapp_numero: string;
  /** Editável no formulário, mas sempre preenchido com 55 de início. */
  codigo_pais?: string;
  cpf?: string | null;
  endereco?: string | null;
}

@Injectable({ providedIn: 'root' })
export class ClientesService {
  private http = inject(HttpClient);

  listar(): Observable<Cliente[]> {
    return this.http.get<Cliente[]>(`${API_URL}/clientes`);
  }

  criar(dados: ClienteCreate): Observable<Cliente> {
    return this.http.post<Cliente>(`${API_URL}/clientes`, dados);
  }
}
