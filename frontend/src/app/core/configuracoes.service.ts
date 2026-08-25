import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export interface Configuracao {
  id: string;
  dias_antecedencia_lembrete: number;
  horario_resumo: string; // "20:00:00"
  resumo_ativo: boolean;
  envio_auto_global: boolean;
}

export type ConfiguracaoUpdate = Partial<Omit<Configuracao, 'id'>>;

@Injectable({ providedIn: 'root' })
export class ConfiguracoesService {
  private http = inject(HttpClient);

  obter(): Observable<Configuracao> {
    return this.http.get<Configuracao>(`${API_URL}/configuracoes`);
  }

  salvar(dados: ConfiguracaoUpdate): Observable<Configuracao> {
    return this.http.patch<Configuracao>(`${API_URL}/configuracoes`, dados);
  }
}
