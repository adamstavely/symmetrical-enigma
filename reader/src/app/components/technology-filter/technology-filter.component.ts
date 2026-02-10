import { Component, input, output, signal, HostListener, inject, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-technology-filter',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './technology-filter.component.html',
  styleUrl: './technology-filter.component.scss',
})
export class TechnologyFilterComponent {
  private readonly el = inject(ElementRef<HTMLElement>);

  readonly options = input<string[]>([]);
  readonly value = input<string>('');
  readonly valueChange = output<string>();

  readonly open = signal(false);

  displayLabel(): string {
    const v = this.value();
    return v || 'All technologies';
  }

  toggle(): void {
    this.open.update((o) => !o);
  }

  select(selected: string): void {
    this.valueChange.emit(selected);
    this.open.set(false);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    const target = event.target as Node;
    if (this.open() && !this.el.nativeElement.contains(target)) {
      this.open.set(false);
    }
  }
}
