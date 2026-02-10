import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { ArchitectureViewComponent } from './pages/architecture-view/architecture-view.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'architecture', component: ArchitectureViewComponent },
  { path: '**', redirectTo: '' },
];
