import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

export interface Vendedor {
  id: string;
  google_email: string;
  nome: string;
  whatsapp_numero: string | null;
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
    window.location.href = `${API_URL}/auth/google/login`;
  }

  me(): Observable<Vendedor> {
    return this.http.get<Vendedor>(`${API_URL}/auth/me`);
  }

  sair(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.logado.set(false);
    this.router.navigate(['/login']);
  }
}
