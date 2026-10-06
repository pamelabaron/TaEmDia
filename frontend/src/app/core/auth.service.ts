import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { API_URL, LOGIN_URL } from './api.config';

export interface Vendedor {
  id: string;
  google_email: string;
  nome: string;
  whatsapp_numero: string | null;
  foto_url: string | null;
  administrador: boolean;
}

const TOKEN_KEY = 'taemdia_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  // Sinal reativo: indica se há sessão ativa (a interface reage a mudanças).
  readonly logado = signal<boolean>(this.temToken());

  private temToken(): boolean {
    return !!localStorage.getItem(TOKEN_KEY);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  salvarToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
    this.logado.set(true);
  }

  /** Inicia o login: envia o navegador ao fluxo OAuth do backend. */
  entrarComGoogle(): void {
    window.location.href = LOGIN_URL;
  }

  /** Só decide o que mostrar no menu. A porta de verdade é o 403 do servidor. */
  readonly administrador = signal<boolean>(false);

  /** Quem está logado, para o bloco da pessoa na barra lateral. */
  readonly vendedor = signal<Vendedor | null>(null);

  /** Iniciais do nome, usadas quando não há foto no Google. */
  readonly iniciais = computed(() => {
    const nome = (this.vendedor()?.nome ?? '').trim();
    if (!nome) return '';
    const partes = nome.split(/\s+/);
    const primeira = partes[0]?.[0] ?? '';
    const ultima = partes.length > 1 ? partes[partes.length - 1][0] : '';
    return (primeira + ultima).toUpperCase();
  });

  me(): Observable<Vendedor> {
    return this.http.get<Vendedor>(`${API_URL}/auth/me`).pipe(
      tap((v) => {
        this.vendedor.set(v);
        this.administrador.set(v.administrador === true);
      }),
    );
  }

  sair(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.logado.set(false);
    this.administrador.set(false);
    this.vendedor.set(null);
    this.router.navigate(['/login']);
  }
}
