import { Component, input, output, signal, HostListener, inject, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-group-filter',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './group-filter.component.html',
  styleUrl: './group-filter.component.scss',
})
export class GroupFilterComponent {
  private readonly el = inject(ElementRef<HTMLElement>);

  readonly options = input<string[]>([]);
  readonly value = input<string>('');
  readonly valueChange = output<string>();

  readonly open = signal(false);

  displayLabel(): string {
    const v = this.value();
    return v || 'All groups';
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
