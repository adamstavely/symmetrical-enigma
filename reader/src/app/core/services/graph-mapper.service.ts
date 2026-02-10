import { Injectable } from '@angular/core';
import type { EnterpriseView, SystemDetail, ContainerDetail } from '../../models/architecture';

export interface CytoscapeElement {
  data: { id: string; label: string; level?: string; parent?: string; vendor?: string; type?: string };
}

/**
 * Maps API responses to Cytoscape elements (nodes + edges).
 * Single source for "API → elements" conversion (DRY).
 */
@Injectable({ providedIn: 'root' })
export class GraphMapperService {
  enterpriseToElements(view: EnterpriseView): { nodes: CytoscapeElement[]; edges: { data: { id: string; source: string; target: string } }[] } {
    const systemIds = new Set((view.systems || []).map((s) => s.id));
    const nodes: CytoscapeElement[] = (view.systems || []).map((s) => ({
      data: {
        id: s.id,
        label: s.name ?? s.id,
        level: 'system',
      },
    }));
    (view.edges || []).forEach((e) => {
      if (!systemIds.has(e.target)) {
        systemIds.add(e.target);
        nodes.push({
          data: {
            id: e.target,
            label: e.target,
            level: 'external',
          },
        });
      }
    });
    const edges = (view.edges || []).map((e, i) => ({
      data: {
        id: `e${i}-${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
      },
    }));
    return { nodes, edges };
  }

  systemToElements(detail: SystemDetail): { nodes: CytoscapeElement[]; edges: { data: { id: string; source: string; target: string } }[] } {
    const nodes: CytoscapeElement[] = [];
    nodes.push({
      data: {
        id: detail.id,
        label: detail.name ?? detail.id,
        level: 'system',
      },
    });
    (detail.containers || []).forEach((c) => {
      nodes.push({
        data: {
          id: c.id,
          label: c.name ?? c.id,
          level: 'container',
          parent: detail.id,
        },
      });
    });
    const edges = (detail.relationships || []).map((r, i) => ({
      data: {
        id: `er${i}-${r.from}-${r.to}`,
        source: (r as { from?: string; to?: string }).from ?? (r as { from?: string; to?: string }).to ?? '',
        target: (r as { from?: string; to?: string }).to ?? (r as { from?: string; to?: string }).from ?? '',
      },
    })).filter((e) => e.data.source && e.data.target);
    return { nodes, edges };
  }

  containerToElements(detail: ContainerDetail): { nodes: CytoscapeElement[]; edges: { data: { id: string; source: string; target: string } }[] } {
    const nodes: CytoscapeElement[] = [{
      data: {
        id: detail.id,
        label: detail.name ?? detail.id,
        level: 'container',
      },
    }];
    (detail.components || []).forEach((c) => {
      nodes.push({
        data: {
          id: c.id,
          label: c.name ?? c.id,
          level: 'component',
        },
      });
    });
    const edges = (detail.dependencies || []).map((d, i) => ({
      data: {
        id: `ed${i}-${detail.id}-${d.target}`,
        source: detail.id,
        target: d.target,
      },
    }));
    return { nodes, edges };
  }
}
