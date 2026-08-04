import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';

/** Anexa o token JWT em toda requisição e trata expiração de sessão (401). */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.getToken();

  const reqAutenticada = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(reqAutenticada).pipe(
    catchError((erro) => {
      if (erro.status === 401) {
        auth.sair();
        router.navigate(['/login']);
      }
      return throwError(() => erro);
    }),
  );
};
