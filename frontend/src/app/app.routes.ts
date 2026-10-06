import { Routes } from '@angular/router';
import { authGuard, visitanteGuard } from './core/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'painel', pathMatch: 'full' },
  {
    path: 'painel',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'login',
    canActivate: [visitanteGuard],
    loadComponent: () => import('./pages/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'auth/callback',
    loadComponent: () => import('./pages/callback/callback.component').then((m) => m.CallbackComponent),
  },
  {
    path: 'clientes',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/clientes/clientes.component').then((m) => m.ClientesComponent),
  },
  {
    path: 'clientes/:id',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/cliente-perfil/cliente-perfil.component').then((m) => m.ClientePerfilComponent),
  },
  {
    path: 'mensagens',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/templates/templates.component').then((m) => m.TemplatesComponent),
  },
  {
    path: 'ranking',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/ranking/ranking.component').then((m) => m.RankingComponent),
  },
  {
    path: 'cobrancas',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/cobrancas/cobrancas.component').then((m) => m.CobrancasComponent),
  },
  // Cada assunto tem endereço e título próprios. "Configurações" deixou de
  // existir como tela e como palavra no endereço.
  {
    path: 'whatsapp',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/configuracoes/whatsapp.component').then((m) => m.ConfigWhatsappComponent),
  },
  {
    path: 'cobranca-automatica',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/configuracoes/cobranca.component').then((m) => m.ConfigCobrancaComponent),
  },
  {
    path: 'resumo-diario',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/configuracoes/resumo.component').then((m) => m.ConfigResumoComponent),
  },

  // Endereços antigos continuam funcionando: link guardado ou aba aberta não
  // pode virar tela de erro por causa de uma troca de nome nossa.
  { path: 'configuracoes', redirectTo: 'whatsapp', pathMatch: 'full' },
  { path: 'configuracoes/whatsapp', redirectTo: 'whatsapp', pathMatch: 'full' },
  { path: 'configuracoes/cobranca', redirectTo: 'cobranca-automatica', pathMatch: 'full' },
  { path: 'configuracoes/resumo', redirectTo: 'resumo-diario', pathMatch: 'full' },
  {
    path: 'minha-assinatura',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/configuracoes/pagina-assinatura.component').then((m) => m.PaginaAssinaturaComponent),
  },
  {
    path: 'assinaturas',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/assinaturas/assinaturas.component').then((m) => m.AssinaturasComponent),
  },
  { path: '**', redirectTo: 'painel' },
];
