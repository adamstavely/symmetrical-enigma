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
import { BreadcrumbComponent } from '../../components/breadcrumb/breadcrumb.component';

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
  ],
  templateUrl: './architecture-view.component.html',
  styleUrl: './architecture-view.component.scss',
})
export class ArchitectureViewComponent implements AfterViewInit {
  @ViewChild(ArchitectureGraphComponent) graphRef!: ArchitectureGraphComponent;

  private readonly state = inject(ArchitectureStateService);
  private readonly graphMapper = inject(GraphMapperService);

  readonly loading = this.state.isLoading;
  readonly error = this.state.errorMessage;
  readonly exportDialogOpen = signal(false);

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
  }

  ngAfterViewInit(): void {
    this.state.loadEnterpriseView().subscribe();
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
