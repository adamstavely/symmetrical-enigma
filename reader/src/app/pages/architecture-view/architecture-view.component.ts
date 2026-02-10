import {
  Component,
  inject,
  ViewChild,
  AfterViewInit,
  signal,
  computed,
  effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { ArchitectureStateService } from '../../core/services/architecture-state.service';
import { GraphMapperService } from '../../core/services/graph-mapper.service';
import {
  ArchitectureGraphComponent,
  type GraphNode,
  type GraphEdge,
} from '../../components/architecture-graph/architecture-graph.component';
import { SystemDetailComponent } from '../../components/system-detail/system-detail.component';
import {
  ExportDialogComponent,
  type ExportFormat,
} from '../../components/export-dialog/export-dialog.component';
import { VersionPickerComponent } from '../../components/version-picker/version-picker.component';
import { VersionDiffComponent } from '../../components/version-diff/version-diff.component';
import { BreadcrumbComponent } from '../../components/breadcrumb/breadcrumb.component';
import { ArchitectureApiService } from '../../core/services/architecture-api.service';
import { take } from 'rxjs/operators';
import type { VersionDiff } from '../../models/architecture';

@Component({
  selector: 'app-architecture-view',
  standalone: true,
  imports: [
    CommonModule,
    BreadcrumbComponent,
    ArchitectureGraphComponent,
    SystemDetailComponent,
    ExportDialogComponent,
    VersionPickerComponent,
    VersionDiffComponent,
  ],
  templateUrl: './architecture-view.component.html',
  styleUrl: './architecture-view.component.scss',
})
export class ArchitectureViewComponent implements AfterViewInit {
  @ViewChild(ArchitectureGraphComponent) graphRef!: ArchitectureGraphComponent;

  private readonly state = inject(ArchitectureStateService);
  private readonly graphMapper = inject(GraphMapperService);
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ArchitectureApiService);

  readonly loading = this.state.isLoading;
  readonly error = this.state.errorMessage;
  readonly exportDialogOpen = signal(false);
  readonly compareWithVersionId = signal<string | null>(null);
  readonly versionDiff = signal<VersionDiff | null>(null);

  readonly graphNodes = computed<GraphNode[]>(() => {
    const ent = this.state.enterprise();
    const sys = this.state.system();
    const cont = this.state.container();
    if (cont) {
      const { nodes } = this.graphMapper.containerToElements(cont);
      return nodes;
    }
    if (sys) {
      const { nodes } = this.graphMapper.systemToElements(sys);
      return nodes;
    }
    if (ent) {
      const { nodes } = this.graphMapper.enterpriseToElements(ent);
      return nodes;
    }
    return [];
  });

  readonly graphEdges = computed<GraphEdge[]>(() => {
    const ent = this.state.enterprise();
    const sys = this.state.system();
    const cont = this.state.container();
    if (cont) return this.graphMapper.containerToElements(cont).edges;
    if (sys) return this.graphMapper.systemToElements(sys).edges;
    if (ent) return this.graphMapper.enterpriseToElements(ent).edges;
    return [];
  });

  readonly system = this.state.system;
  readonly container = this.state.container;
  readonly systemId = this.state.systemId;
  readonly versionId = this.state.versionId;
  readonly versions = this.state.versions;

  constructor() {
    effect(() => {
      this.state.enterprise();
      this.state.system();
      this.state.container();
    });
    effect(() => {
      const sid = this.state.systemId();
      const toId = this.state.versionId();
      const fromId = this.compareWithVersionId();
      if (sid && fromId && toId && fromId !== toId) {
        this.api
          .getVersionDiff(sid, fromId, toId)
          .pipe(take(1))
          .subscribe({
            next: (d) => this.versionDiff.set(d ?? null),
            error: () => this.versionDiff.set(null),
          });
      } else {
        this.versionDiff.set(null);
      }
    });
  }

  ngAfterViewInit(): void {
    const technology = this.route.snapshot.queryParamMap.get('technology') ?? undefined;
    this.state.loadEnterpriseView(technology).subscribe(() => {
      const systemId = this.route.snapshot.queryParamMap.get('system');
      if (systemId) {
        this.state.loadSystemDetail(systemId).subscribe();
        this.state.loadSystemVersions(systemId);
      }
    });
  }

  onNodeSelect(event: { id: string; level?: string }): void {
    const level = event.level ?? 'system';
    const systemId = this.state.systemId();
    if (level === 'system') {
      this.state.loadSystemDetail(event.id).subscribe();
      this.state.loadSystemVersions(event.id);
    } else if (level === 'container' && systemId) {
      this.state.loadContainerDetail(systemId, event.id).subscribe();
    }
  }

  onVersionSelect(versionId: string): void {
    const sid = this.state.systemId();
    if (sid) this.state.loadSystemDetail(sid, versionId).subscribe();
  }

  onVersionClear(): void {
    const sid = this.state.systemId();
    if (sid) this.state.loadSystemDetail(sid).subscribe();
    this.compareWithVersionId.set(null);
  }

  onCompareSelect(versionId: string | null): void {
    this.compareWithVersionId.set(versionId);
  }

  versionLabel(versionId: string): string {
    const v = this.state.versions().find((x) => x.id === versionId);
    if (!v) return versionId;
    try {
      const d = v.analyzed_at ? new Date(v.analyzed_at).toLocaleString() : '';
      return v.commit_sha ? `${d} (${v.commit_sha.slice(0, 7)})` : d;
    } catch {
      return versionId;
    }
  }

  onContainerSelect(containerId: string): void {
    const systemId = this.state.systemId();
    if (systemId) this.state.loadContainerDetail(systemId, containerId).subscribe();
  }

  openExport(): void {
    this.exportDialogOpen.set(true);
  }

  onExportFormat(format: ExportFormat): void {
    const graph = this.graphRef;
    if (!graph) return;
    if (format === 'png') {
      const dataUrl = graph.exportPng();
      if (dataUrl) this.downloadDataUrl(dataUrl, 'edda-architecture.png');
    } else if (format === 'svg') {
      const svg = graph.exportSvg();
      if (svg) {
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        this.downloadUrl(url, 'edda-architecture.svg');
        URL.revokeObjectURL(url);
      }
    } else if (format === 'pdf') {
      const dataUrl = graph.exportPng();
      if (dataUrl) {
        import('jspdf').then(({ default: jsPDF }) => {
          const doc = new jsPDF({ orientation: 'l', unit: 'px' });
          const img = new Image();
          img.onload = () => {
            const w = doc.internal.pageSize.getWidth();
            const h = doc.internal.pageSize.getHeight();
            doc.addImage(img.src, 'PNG', 0, 0, w, h);
            doc.save('edda-architecture.pdf');
          };
          img.src = dataUrl;
        }).catch(() => this.downloadDataUrl(dataUrl, 'edda-architecture.png'));
      }
    }
    this.exportDialogOpen.set(false);
  }

  onExportClosed(): void {
    this.exportDialogOpen.set(false);
  }

  private downloadDataUrl(dataUrl: string, filename: string): void {
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = filename;
    a.click();
  }

  private downloadUrl(url: string, filename: string): void {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  }
}
