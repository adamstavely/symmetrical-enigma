import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ArchitectureApiService } from '../../core/services/architecture-api.service';

@Component({
  selector: 'app-inventory',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './inventory.component.html',
  styleUrl: './inventory.component.scss',
})
export class InventoryComponent implements OnInit {
  private readonly api = inject(ArchitectureApiService);

  readonly inventory = signal<Array<{ technology: string; system_ids: string[] }>>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.api
      .getTechnologyInventory()
      .subscribe({
        next: (data) => {
          this.inventory.set(data);
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set(err?.message ?? 'Failed to load technology inventory');
          this.loading.set(false);
        },
      });
  }
}
