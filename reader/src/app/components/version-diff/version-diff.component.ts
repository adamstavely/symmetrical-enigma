import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import type { VersionDiff } from '../../models/architecture';

@Component({
  selector: 'app-version-diff',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './version-diff.component.html',
  styleUrl: './version-diff.component.scss',
})
export class VersionDiffComponent {
  @Input() diff: VersionDiff | null = null;
  @Input() fromLabel = '';
  @Input() toLabel = '';
}
