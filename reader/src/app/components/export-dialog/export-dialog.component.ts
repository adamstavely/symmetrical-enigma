import { Component, output, input } from '@angular/core';
import { CommonModule } from '@angular/common';

export type ExportFormat = 'png' | 'svg' | 'pdf';

@Component({
  selector: 'app-export-dialog',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './export-dialog.component.html',
  styleUrl: './export-dialog.component.scss',
})
export class ExportDialogComponent {
  readonly exportFormat = output<ExportFormat>();
  readonly closed = output<void>();
  readonly open = input<boolean>(false);

  close(): void {
    this.closed.emit();
  }

  choose(format: ExportFormat): void {
    this.exportFormat.emit(format);
    this.closed.emit();
  }
}
