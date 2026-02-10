import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { ArchitectureViewComponent } from './pages/architecture-view/architecture-view.component';
import { ReferenceComponent } from './pages/reference/reference.component';
import { DriftComponent } from './pages/drift/drift.component';
import { InventoryComponent } from './pages/inventory/inventory.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'architecture', component: ArchitectureViewComponent },
  { path: 'drift', component: DriftComponent },
  { path: 'inventory', component: InventoryComponent },
  { path: 'reference', component: ReferenceComponent },
  { path: '**', redirectTo: '' },
];
