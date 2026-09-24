import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';
import { AssinaturaNecessariaDialog } from './assinatura-necessaria.dialog';

/** Evita empilhar diálogos quando a tela dispara várias chamadas de uma vez. */
let dialogoAberto = false;

/**
 * Anexa o token JWT em toda requisição e trata duas respostas de forma única:
 *
 * - **401**: a sessão caiu. Encerra e volta para a apresentação.
 * - **402**: a assinatura venceu. Quem decide isso é o servidor; aqui só
 *   traduzimos a recusa em uma mensagem com o caminho para resolver.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const dialog = inject(MatDialog);
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

      // O diálogo responde a uma AÇÃO da pessoa. Uma leitura que falha ao
      // abrir a tela (o cartão do WhatsApp, por exemplo) não deve abrir nada:
      // a própria tela mostra que aquilo depende de assinatura.
      const foiAcao = req.method !== 'GET';

      if (erro.status === 402 && foiAcao && !dialogoAberto) {
        dialogoAberto = true;
        dialog
          .open(AssinaturaNecessariaDialog, {
            width: '440px',
            maxWidth: 'calc(100vw - 32px)',
            data: {
              mensagem:
                erro.error?.detail ?? 'Sua assinatura venceu. Renove para continuar.',
            },
          })
          .afterClosed()
          .subscribe(() => (dialogoAberto = false));
      }

      return throwError(() => erro);
    }),
  );
};
