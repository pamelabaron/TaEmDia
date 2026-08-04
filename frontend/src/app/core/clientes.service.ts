import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export interface Cliente {
  id: string;
  nome: string;
  whatsapp_numero: string;
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
