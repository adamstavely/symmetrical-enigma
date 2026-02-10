import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ArchitectureApiService } from '../../core/services/architecture-api.service';
import { ArchitectureStateService } from '../../core/services/architecture-state.service';
import type { SearchResultItem } from '../../models/architecture';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './search-bar.component.html',
  styleUrl: './search-bar.component.scss',
})
export class SearchBarComponent {
  private readonly api = inject(ArchitectureApiService);
  private readonly state = inject(ArchitectureStateService);
  private readonly router = inject(Router);

  readonly query = signal('');
  readonly groupFilter = signal<string>('');
  readonly results = signal<SearchResultItem[]>([]);
  readonly loading = signal(false);
  readonly open = signal(false);
  readonly groups = signal<string[]>([]);

  private readonly search$ = new Subject<string>();

  constructor() {
    this.api.getGroups().subscribe((g) => this.groups.set(g));
    this.search$
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap((q) => {
          this.loading.set(true);
          return this.api.search(q, this.groupFilter() ? { group: this.groupFilter() } : undefined);
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

  onGroupChange(value: string): void {
    this.groupFilter.set(value);
    const q = this.query();
    if (q.trim().length >= 2) this.search$.next(q.trim());
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
