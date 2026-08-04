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
