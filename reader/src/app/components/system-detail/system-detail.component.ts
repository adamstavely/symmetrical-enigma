import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import type { SystemDetail, ContainerDetail } from '../../models/architecture';

@Component({
  selector: 'app-system-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './system-detail.component.html',
  styleUrl: './system-detail.component.scss',
})
export class SystemDetailComponent {
  @Input() system: SystemDetail | null = null;
  @Input() container: ContainerDetail | null = null;
  @Output() containerSelect = new EventEmitter<string>();

  onContainerClick(containerId: string): void {
    this.containerSelect.emit(containerId);
  }
}
