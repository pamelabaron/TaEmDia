import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export interface RecebimentoMes {
  mes: string;
  total: number;
}

export interface ClienteEmAtraso {
  id: string;
  nome: string;
  valor_atrasado: number;
}

export interface Dashboard {
  total_a_receber: number;
  recebido_no_mes: number;
  em_atraso: number;
  clientes_inadimplentes: number;
  recebimentos_mensais: RecebimentoMes[];
  clientes_em_atraso: ClienteEmAtraso[];
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private http = inject(HttpClient);

  carregar(): Observable<Dashboard> {
    return this.http.get<Dashboard>(`${API_URL}/relatorios/dashboard`);
  }
}
