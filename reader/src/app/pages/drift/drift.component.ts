import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ArchitectureApiService } from '../../core/services/architecture-api.service';
import { AnalyzeDialogComponent } from '../../components/analyze-dialog/analyze-dialog.component';
import type { DriftAlert } from '../../models/architecture';

@Component({
  selector: 'app-drift',
  standalone: true,
  imports: [CommonModule, RouterLink, AnalyzeDialogComponent],
  templateUrl: './drift.component.html',
  styleUrl: './drift.component.scss',
})
export class DriftComponent {
  private readonly api = inject(ArchitectureApiService);

  readonly alerts = signal<DriftAlert[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly reAnalyzing = signal<string | null>(null);
  readonly analyzeDialogOpen = signal(false);

  readonly minSeverity = signal<string>('');

  ngOnInit(): void {
    this.loadDrift();
  }

  loadDrift(): void {
    this.loading.set(true);
    this.error.set(null);
    const min = this.minSeverity() || undefined;
    this.api.getDriftAlerts({ min_severity: min, limit: 200 }).subscribe({
      next: (a) => {
        this.alerts.set(a);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? err?.message ?? 'Failed to load drift');
        this.loading.set(false);
      },
    });
  }

  reAnalyze(alert: DriftAlert): void {
    const url = alert.repository_url ?? '';
    if (!url) return;
    this.reAnalyzing.set(alert.system_id);
    this.api.analyzeRepository(url).subscribe({
      next: () => {
        this.reAnalyzing.set(null);
        this.loadDrift();
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? err?.message ?? 'Re-analyze failed');
        this.reAnalyzing.set(null);
      },
    });
  }

  openAnalyzeDialog(): void {
    this.analyzeDialogOpen.set(true);
  }

  onAnalyzeDone(): void {
    this.analyzeDialogOpen.set(false);
    this.loadDrift();
  }

  severityClass(severity: string): string {
    return `severity-${severity}`;
  }

  formatDate(iso: string | null): string {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });
    } catch {
      return iso;
    }
  }

  formatHours(hours: number): string {
    if (hours >= 24) return `${Math.round(hours / 24)}d`;
    return `${Math.round(hours)}h`;
  }
}
