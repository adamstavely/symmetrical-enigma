import {
  Component,
  Input,
  Output,
  EventEmitter,
  inject,
  OnDestroy,
  AfterViewInit,
  ViewChild,
  ElementRef,
  signal,
  effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import cytoscape, { type Core, type NodeSingular } from 'cytoscape';
import { GraphStyleService } from '../../core/services/graph-style.service';

export interface GraphNode {
  data: { id: string; label: string; level?: string; parent?: string; vendor?: string; type?: string };
}

export interface GraphEdge {
  data: { id: string; source: string; target: string };
}

@Component({
  selector: 'app-architecture-graph',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './architecture-graph.component.html',
  styleUrl: './architecture-graph.component.scss',
  host: { class: 'graph-host' },
})
export class ArchitectureGraphComponent implements AfterViewInit, OnDestroy {
  @ViewChild('cyContainer') cyContainer!: ElementRef<HTMLDivElement>;

  @Input() set nodes(value: GraphNode[]) {
    this.nodesSet.set(value ?? []);
  }
  @Input() set edges(value: GraphEdge[]) {
    this.edgesSet.set(value ?? []);
  }
  @Output() nodeSelect = new EventEmitter<{ id: string; level?: string }>();

  private readonly styleService = inject(GraphStyleService);
  readonly nodesSet = signal<GraphNode[]>([]);
  private readonly edgesSet = signal<GraphEdge[]>([]);

  private cy: Core | null = null;
  readonly loading = signal(true);

  constructor() {
    effect(() => {
      const n = this.nodesSet();
      const e = this.edgesSet();
      if (this.cy && n.length > 0) {
        this.cy.elements().remove();
        const elements = [
          ...n.map((node) => ({ group: 'nodes' as const, data: node.data })),
          ...e.map((edge) => ({ group: 'edges' as const, data: edge.data })),
        ];
        this.cy.add(elements);
        this.cy.layout({ name: 'cose', animate: true }).run();
      }
    });
  }

  ngAfterViewInit(): void {
    const el = this.cyContainer?.nativeElement;
    if (!el) return;
    const styles = this.styleService.buildStyles();
    this.cy = cytoscape({
      container: el,
      style: styles,
      elements: [],
      layout: { name: 'cose' },
      minZoom: 0.2,
      maxZoom: 4,
      wheelSensitivity: 0.3,
    });
    this.cy.on('tap', 'node', (evt) => {
      const node = evt.target as NodeSingular;
      const id = node.data('id');
      const level = node.data('level');
      this.nodeSelect.emit({ id, level });
    });
    this.loading.set(false);
  }

  ngOnDestroy(): void {
    this.cy?.destroy();
    this.cy = null;
  }

  exportPng(): string | null {
    if (!this.cy) return null;
    return this.cy.png({ scale: 2, full: true });
  }

  exportSvg(): string | null {
    if (!this.cy) return null;
    return (this.cy as unknown as { svg: (opts: { scale?: number; full?: boolean }) => string }).svg({
      scale: 2,
      full: true,
    });
  }
}
