import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export type CanalResumo = 'whatsapp' | 'email' | 'ambos';

export interface Configuracao {
  id: string;
  dias_antecedencia_lembrete: number;
  horario_resumo: string; // "20:00:00"
  resumo_ativo: boolean;
  envio_auto_global: boolean;
  canal_resumo: CanalResumo;
  email_resumo: string | null;
  whatsapp_resumo: string | null;
}

/** Os números de um dia, como a API devolve. */
export interface ResumoDoDia {
  dia: string;
  houve_atividade: boolean;
  cobrancas_enviadas: number;
  cobrancas_falharam: number;
  pagamentos: number;
  valor_recebido: number;
  sem_resposta: number;
  respostas: Record<string, number>;
  rotulos: Record<string, string>;
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

  /** Datas que o filtro pode oferecer. Quem decide a janela é o servidor. */
  diasDoResumo(): Observable<string[]> {
    return this.http.get<string[]>(`${API_URL}/relatorios/resumo/dias`);
  }

  resumoDoDia(dia: string): Observable<ResumoDoDia> {
    return this.http.get<ResumoDoDia>(`${API_URL}/relatorios/resumo`, { params: { dia } });
  }

  resumoEmPdf(dia: string): Observable<Blob> {
    return this.http.get(`${API_URL}/relatorios/resumo/pdf`, {
      params: { dia },
      responseType: 'blob',
    });
  }
}
