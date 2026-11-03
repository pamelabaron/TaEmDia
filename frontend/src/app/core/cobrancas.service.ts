import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export interface CobrancaLog {
  id: string;
  cliente_id: string | null;
  cliente_nome: string;
  parcela_id: string | null;
  tipo: string;
  conteudo: string;
  status: string;
  criado_em: string;
}

export interface StatusWhatsApp {
  conectado: boolean;
  numero: string | null;
  qrcode: string | null;
  detalhe: string;
  modo_simulador: boolean;
}

@Injectable({ providedIn: 'root' })
export class CobrancasService {
  private http = inject(HttpClient);

  listar(periodo: 'hoje' | 'semana' | 'mes'): Observable<CobrancaLog[]> {
    return this.http.get<CobrancaLog[]>(`${API_URL}/cobrancas?periodo=${periodo}`);
  }

  dispararManual(parcelaId: string): Observable<CobrancaLog> {
    return this.http.post<CobrancaLog>(`${API_URL}/cobrancas/${parcelaId}/disparar`, {});
  }

  statusWhatsApp(): Observable<StatusWhatsApp> {
    return this.http.get<StatusWhatsApp>(`${API_URL}/whatsapp/status`);
  }

  desconectarWhatsApp(): Observable<void> {
    return this.http.post<void>(`${API_URL}/whatsapp/desconectar`, {});
  }
}
