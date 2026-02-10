import { Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { SearchBarComponent } from './components/search-bar/search-bar.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, SearchBarComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {}
