import { Component, inject, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ArchitectureApiService } from '../../core/services/architecture-api.service';

@Component({
  selector: 'app-analyze-dialog',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analyze-dialog.component.html',
  styleUrl: './analyze-dialog.component.scss',
})
export class AnalyzeDialogComponent {
  private readonly api = inject(ArchitectureApiService);

  readonly done = output<void>();
  readonly cancel = output<void>();

  readonly repositoryUrl = signal('');
  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  submit(): void {
    const url = this.repositoryUrl().trim();
    if (!url) {
      this.error.set('Enter a repository URL');
      return;
    }
    this.error.set(null);
    this.submitting.set(true);
    this.api.analyzeRepository(url).subscribe({
      next: () => {
        this.submitting.set(false);
        this.done.emit();
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? err?.message ?? 'Analysis failed');
        this.submitting.set(false);
      },
    });
  }

  close(): void {
    this.cancel.emit();
  }
}
