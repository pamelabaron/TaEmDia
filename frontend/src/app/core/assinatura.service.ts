import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { API_URL } from './api.config';

export interface Pagamento {
  id: string;
  valor: number;
  arquivo_nome: string;
  situacao: 'pendente' | 'aprovado' | 'recusado';
  enviado_em: string;
  avaliado_em: string | null;
  observacao: string | null;
}

/** Situações que a administração consulta: a fila e o histórico. */
export type SituacaoComprovante = 'pendente' | 'aprovado' | 'recusado';

export interface ComprovanteAdmin extends Pagamento {
  vendedor_id: string;
  vendedor_nome: string;
  vendedor_email: string;
}

export interface MinhaAssinatura {
  situacao: 'em_teste' | 'ativa' | 'vencida';
  valido_ate: string | null;
  dias_restantes: number;
  tem_pendente: boolean;
  valor_mensal: number;
  pix_chave: string;
  pix_nome: string;
  historico: Pagamento[];
}

@Injectable({ providedIn: 'root' })
export class AssinaturaService {
  private http = inject(HttpClient);

  /** Situação conhecida da assinatura, para a faixa de aviso no topo. */
  readonly atual = signal<MinhaAssinatura | null>(null);

  readonly bloqueada = computed(() => this.atual()?.situacao === 'vencida');

  /** Quantos dias faltam, quando o período está acabando (5 dias ou menos). */
  readonly acabando = computed(() => {
    const a = this.atual();
    if (!a || a.situacao !== 'em_teste') return 0;
    return a.dias_restantes <= 5 ? a.dias_restantes : 0;
  });

  carregar(): Observable<MinhaAssinatura> {
    return this.http
      .get<MinhaAssinatura>(`${API_URL}/assinatura`)
      .pipe(tap((a) => this.atual.set(a)));
  }

  enviarComprovante(valor: number, arquivo: File): Observable<Pagamento> {
    const dados = new FormData();
    dados.append('valor', String(valor));
    dados.append('arquivo', arquivo);
    return this.http.post<Pagamento>(`${API_URL}/assinatura/comprovante`, dados);
  }

  // ------------------------------------------------------------ administração

  /** Fila (pendente) ou histórico (aprovado, recusado). */
  listar(situacao: SituacaoComprovante): Observable<ComprovanteAdmin[]> {
    return this.http.get<ComprovanteAdmin[]>(`${API_URL}/admin/comprovantes`, {
      params: { situacao },
    });
  }

  /** O arquivo sai por endpoint autenticado — nunca por caminho público. */
  baixarComprovante(id: string): Observable<Blob> {
    return this.http.get(`${API_URL}/admin/comprovantes/${id}/arquivo`, {
      responseType: 'blob',
    });
  }

  aprovar(id: string): Observable<Pagamento> {
    return this.http.post<Pagamento>(`${API_URL}/admin/comprovantes/${id}/aprovar`, {});
  }

  recusar(id: string, motivo: string): Observable<Pagamento> {
    return this.http.post<Pagamento>(`${API_URL}/admin/comprovantes/${id}/recusar`, { motivo });
  }
}
