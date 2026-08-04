import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Template, TemplatesService } from '../../core/templates.service';

const VARIAVEIS = ['nome_cliente', 'valor_parcela', 'data_vencimento', 'dias_atraso'];
const EXEMPLO: Record<string, string> = {
  nome_cliente: 'Maria Silva',
  valor_parcela: 'R$ 100,00',
  data_vencimento: '10/08/2026',
  dias_atraso: '3',
};
const TIPO_LABEL: Record<string, string> = {
  lembrete: 'Lembrete (antes do vencimento)',
  vencimento: 'No dia do vencimento',
  atraso: 'Parcela em atraso',
};

@Component({
  selector: 'app-templates',
  standalone: true,
  imports: [
    FormsModule, MatCardModule, MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSlideToggleModule, MatChipsModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="pagina">
      <h2>Mensagens de cobrança</h2>
      <p class="ajuda">
        Personalize as mensagens que o sistema enviará. Use as variáveis abaixo — elas
        serão trocadas pelos dados reais de cada cliente na hora do envio.
      </p>

      @if (carregando()) {
        <div class="centro"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        @for (t of templates; track t.id) {
          <mat-card class="tpl">
            <div class="tpl-topo">
              <span class="tipo">{{ rotuloTipo(t.tipo) }}</span>
              <mat-slide-toggle [(ngModel)]="t.ativo" [name]="'ativo-' + t.id">Ativo</mat-slide-toggle>
            </div>

            <mat-form-field appearance="outline" class="campo">
              <mat-label>Título</mat-label>
              <input matInput [(ngModel)]="t.titulo" [name]="'titulo-' + t.id" />
            </mat-form-field>

            <mat-form-field appearance="outline" class="campo">
              <mat-label>Mensagem</mat-label>
              <textarea matInput rows="3" [(ngModel)]="t.corpo" [name]="'corpo-' + t.id"></textarea>
            </mat-form-field>

            <div class="variaveis">
              <span class="rot">Inserir variável:</span>
              @for (v of variaveis; track v) {
                <button mat-stroked-button class="chip-var" (click)="inserir(t, v)">+ {{ '{' + v + '}' }}</button>
              }
            </div>

            <div class="preview">
              <span class="rot">Prévia:</span>
              <p>{{ renderizar(t.corpo) }}</p>
            </div>

            <button mat-raised-button color="primary" [disabled]="salvando()" (click)="salvar(t)">
              <mat-icon>save</mat-icon> Salvar
            </button>
          </mat-card>
        }
      }
    </div>
  `,
  styles: [`
    .pagina { max-width: 760px; margin: 0 auto; padding: 16px; }
    .ajuda { color: #666; margin-bottom: 16px; }
    .centro { display: flex; justify-content: center; padding: 32px; }
    .tpl { padding: 16px; margin-bottom: 20px; }
    .tpl-topo { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .tipo { font-weight: 600; color: #1565c0; }
    .campo { width: 100%; }
    .variaveis { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
    .variaveis .rot { color: #777; font-size: 0.85rem; }
    .chip-var { font-size: 0.75rem; min-width: 0; padding: 0 10px; line-height: 30px; }
    .preview { background: #e7f3ff; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; }
    .preview .rot { font-size: 0.75rem; color: #1565c0; font-weight: 500; }
    .preview p { margin: 4px 0 0; white-space: pre-wrap; }
  `],
})
export class TemplatesComponent implements OnInit {
  private service = inject(TemplatesService);
  private snack = inject(MatSnackBar);

  templates: Template[] = [];
  readonly carregando = signal<boolean>(true);
  readonly salvando = signal<boolean>(false);
  readonly variaveis = VARIAVEIS;

  ngOnInit(): void {
    this.service.listar().subscribe({
      next: (lista) => { this.templates = lista; this.carregando.set(false); },
      error: () => { this.carregando.set(false); this.snack.open('Erro ao carregar mensagens.', 'OK', { duration: 4000 }); },
    });
  }

  rotuloTipo(tipo: string): string { return TIPO_LABEL[tipo] ?? tipo; }

  inserir(t: Template, v: string): void {
    t.corpo = (t.corpo ?? '') + `{${v}}`;
  }

  renderizar(corpo: string): string {
    let r = corpo ?? '';
    for (const v of VARIAVEIS) r = r.replaceAll(`{${v}}`, EXEMPLO[v]);
    return r;
  }

  salvar(t: Template): void {
    this.salvando.set(true);
    this.service.editar(t.id, { titulo: t.titulo, corpo: t.corpo, ativo: t.ativo }).subscribe({
      next: () => { this.salvando.set(false); this.snack.open('Mensagem salva!', 'OK', { duration: 3000 }); },
      error: () => { this.salvando.set(false); this.snack.open('Erro ao salvar.', 'OK', { duration: 4000 }); },
    });
  }
}
