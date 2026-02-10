import { Component, inject, signal, input, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ArchitectureApiService } from '../../core/services/architecture-api.service';
import { ArchitectureStateService } from '../../core/services/architecture-state.service';
import type { SearchResultItem } from '../../models/architecture';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './search-bar.component.html',
  styleUrl: './search-bar.component.scss',
})
export class SearchBarComponent {
  private readonly api = inject(ArchitectureApiService);
  private readonly state = inject(ArchitectureStateService);
  private readonly router = inject(Router);

  readonly groupFilter = input<string>('');
  readonly technologyFilter = input<string>('');

  readonly query = signal('');
  readonly results = signal<SearchResultItem[]>([]);
  readonly loading = signal(false);
  readonly open = signal(false);

  private readonly search$ = new Subject<string>();

  constructor() {
    effect(() => {
      this.groupFilter();
      this.technologyFilter();
      const q = this.query().trim();
      if (q.length >= 2) this.search$.next(q);
    });
    this.search$
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap((q) => {
          this.loading.set(true);
          const filters: { group?: string; technology?: string } = {};
          const g = this.groupFilter();
          const t = this.technologyFilter();
          if (g) filters.group = g;
          if (t) filters.technology = t;
          return this.api.search(q, Object.keys(filters).length ? filters : undefined);
        })
      )
      .subscribe({
        next: (r) => {
          this.results.set(r);
          this.loading.set(false);
          this.open.set(true);
        },
        error: () => this.loading.set(false),
      });
  }

  onInput(value: string): void {
    this.query.set(value);
    if (value.trim().length >= 2) {
      this.search$.next(value.trim());
    } else {
      this.results.set([]);
      this.open.set(false);
    }
  }

  selectResult(item: SearchResultItem): void {
    this.open.set(false);
    this.results.set([]);
    if (item.type === 'system') {
      this.state.loadSystemDetail(item.id).subscribe(() => this.router.navigate(['/']));
    }
  }

  closeDropdown(): void {
    this.open.set(false);
  }
}
