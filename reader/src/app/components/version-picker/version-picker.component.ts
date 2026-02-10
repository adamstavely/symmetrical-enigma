import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import type { ArchitectureVersion } from '../../models/architecture';

@Component({
  selector: 'app-version-picker',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './version-picker.component.html',
  styleUrl: './version-picker.component.scss',
})
export class VersionPickerComponent {
  @Input() versions: ArchitectureVersion[] = [];
  @Input() selectedVersionId: string | null = null;
  @Input() compareWithVersionId: string | null = null;
  @Input() loading = false;
  @Output() versionSelect = new EventEmitter<string>();
  @Output() clearVersion = new EventEmitter<void>();
  @Output() compareSelect = new EventEmitter<string | null>();

  onSelectChange(event: Event): void {
    const el = event.target as HTMLSelectElement;
    const id = el?.value ?? '';
    if (id) this.versionSelect.emit(id);
    else this.clearVersion.emit();
  }

  onCompareChange(event: Event): void {
    const el = event.target as HTMLSelectElement;
    const id = el?.value ?? '';
    this.compareSelect.emit(id || null);
  }

  onClear(): void {
    this.clearVersion.emit();
  }

  formatDate(analyzed_at?: string): string {
    if (!analyzed_at) return '';
    try {
      const d = new Date(analyzed_at);
      return isNaN(d.getTime()) ? analyzed_at : d.toLocaleString();
    } catch {
      return analyzed_at;
    }
  }
}
