import { Routes } from '@angular/router';
import { authGuard } from './core/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'painel', pathMatch: 'full' },
  {
    path: 'painel',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'login',
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
  { path: '**', redirectTo: 'painel' },
];
