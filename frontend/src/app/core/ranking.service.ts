import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export interface RankingCliente {
  id: string;
  nome: string;
  classificacao: 'bom' | 'regular' | 'inadimplente' | 'sem_historico';
  percentual_em_dia: number;
  media_dias_atraso: number;
  total_avaliadas: number;
}

export interface Ranking {
  bons: number;
  regulares: number;
  inadimplentes: number;
  sem_historico: number;
  clientes: RankingCliente[];
}

@Injectable({ providedIn: 'root' })
export class RankingService {
  private http = inject(HttpClient);

  carregar(meses = 12): Observable<Ranking> {
    return this.http.get<Ranking>(`${API_URL}/relatorios/ranking?meses=${meses}`);
  }
}
