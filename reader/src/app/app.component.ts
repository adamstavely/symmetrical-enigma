import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { SearchBarComponent } from './components/search-bar/search-bar.component';
import { GroupFilterComponent } from './components/group-filter/group-filter.component';
import { TechnologyFilterComponent } from './components/technology-filter/technology-filter.component';
import { ArchitectureApiService } from './core/services/architecture-api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterLink,
    SearchBarComponent,
    GroupFilterComponent,
    TechnologyFilterComponent,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  private readonly api = inject(ArchitectureApiService);

  readonly groupFilter = signal<string>('');
  readonly technologyFilter = signal<string>('');
  readonly groups = signal<string[]>([]);
  readonly technologies = signal<string[]>([]);

  constructor() {
    this.api.getGroups().subscribe((g) => this.groups.set(g));
    this.api.getTechnologies().subscribe((t) => this.technologies.set(t));
  }

  setGroupFilter(value: string): void {
    this.groupFilter.set(value);
  }

  setTechnologyFilter(value: string): void {
    this.technologyFilter.set(value);
  }
}
