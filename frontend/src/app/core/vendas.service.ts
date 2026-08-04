import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export interface Parcela {
  id: string;
  numero_parcela: number;
  valor: number;
  data_vencimento: string;
  data_pagamento: string | null;
  status: 'pendente' | 'atrasada' | 'aguardando_confirmacao' | 'paga';
}

export interface Venda {
  id: string;
  cliente_id: string;
  valor_total: number;
  num_parcelas: number;
  data_primeira_parcela: string;
  status: 'ativa' | 'cancelada';
  criado_em: string;
  parcelas: Parcela[];
}

export interface PerfilCliente {
  id: string;
  nome: string;
  whatsapp_numero: string;
  cpf: string | null;
  endereco: string | null;
  saldo_devedor: number;
  vendas: Venda[];
}

export interface VendaCreate {
  cliente_id: string;
  valor_total: number;
  num_parcelas: number;
  data_primeira_parcela: string;
}

@Injectable({ providedIn: 'root' })
export class VendasService {
  private http = inject(HttpClient);

  perfil(clienteId: string): Observable<PerfilCliente> {
    return this.http.get<PerfilCliente>(`${API_URL}/clientes/${clienteId}/perfil`);
  }

  registrarVenda(dados: VendaCreate): Observable<Venda> {
    return this.http.post<Venda>(`${API_URL}/vendas`, dados);
  }

  pagarParcela(parcelaId: string): Observable<Parcela> {
    return this.http.post<Parcela>(`${API_URL}/parcelas/${parcelaId}/pagar`, {});
  }

  cancelarVenda(vendaId: string): Observable<Venda> {
    return this.http.post<Venda>(`${API_URL}/vendas/${vendaId}/cancelar`, {});
  }
}
