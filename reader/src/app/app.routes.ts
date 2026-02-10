import { Routes } from '@angular/router';
import { ArchitectureViewComponent } from './pages/architecture-view/architecture-view.component';

export const routes: Routes = [
  { path: '', component: ArchitectureViewComponent },
  { path: '**', redirectTo: '' },
];
