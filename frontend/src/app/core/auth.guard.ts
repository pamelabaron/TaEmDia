import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/** Impede o acesso a páginas internas sem estar autenticado (RN01). */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.logado()) {
    return true;
  }
  router.navigate(['/login']);
  return false;
};

/**
 * Mantém quem já tem sessão fora da página de apresentação: ali o cabeçalho da
 * landing e a barra do aplicativo apareceriam ao mesmo tempo, com dois menus na
 * tela. Quem já entrou vai direto para o painel.
 */
export const visitanteGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.logado()) {
    return true;
  }
  router.navigate(['/painel']);
  return false;
};
