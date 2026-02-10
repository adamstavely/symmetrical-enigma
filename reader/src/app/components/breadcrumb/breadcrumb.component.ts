import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ArchitectureStateService } from '../../core/services/architecture-state.service';

@Component({
  selector: 'app-breadcrumb',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './breadcrumb.component.html',
  styleUrl: './breadcrumb.component.scss',
})
export class BreadcrumbComponent {
  private readonly state = inject(ArchitectureStateService);

  readonly level = this.state.level;
  readonly systemId = this.state.systemId;
  readonly containerId = this.state.containerId;
  readonly system = this.state.system;
  readonly container = this.state.container;

  goToEnterprise(): void {
    this.state.loadEnterpriseView().subscribe();
  }

  goToSystem(): void {
    const id = this.state.systemId();
    if (id) this.state.loadSystemDetail(id).subscribe();
  }
}
