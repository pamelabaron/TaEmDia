import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export interface Template {
  id: string;
  tipo: 'lembrete' | 'vencimento' | 'atraso';
  titulo: string;
  corpo: string;
  is_padrao: boolean;
  ativo: boolean;
}

export interface TemplateUpdate {
  titulo?: string;
  corpo?: string;
  ativo?: boolean;
}

@Injectable({ providedIn: 'root' })
export class TemplatesService {
  private http = inject(HttpClient);

  listar(): Observable<Template[]> {
    return this.http.get<Template[]>(`${API_URL}/templates`);
  }

  editar(id: string, dados: TemplateUpdate): Observable<Template> {
    return this.http.patch<Template>(`${API_URL}/templates/${id}`, dados);
  }
}
