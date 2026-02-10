import { Injectable } from '@angular/core';
import type { StylesheetStyle } from 'cytoscape';

/**
 * Builds Cytoscape stylesheet from design tokens.
 * Single source for graph visual styling (DRY).
 */
@Injectable({ providedIn: 'root' })
export class GraphStyleService {
  buildStyles(): StylesheetStyle[] {
    return [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'text-valign': 'bottom',
          'text-halign': 'center',
          'color': 'var(--graph-node-label-color)',
          'font-size': 13,
          'text-margin-y': 6,
          'width': 'var(--graph-node-width)',
          'height': 'var(--graph-node-height)',
          'background-color': 'var(--graph-node-system-fill)',
          'border-color': 'var(--graph-node-system-border)',
          'border-width': 2,
          'border-opacity': 1,
          'shape': 'round-rectangle',
        },
      },
      {
        selector: 'node[level="system"]',
        style: {
          'background-color': 'var(--graph-node-system-fill)',
          'border-color': 'var(--graph-node-system-border)',
          'shape': 'round-rectangle',
        },
      },
      {
        selector: 'node[level="container"]',
        style: {
          'background-color': 'var(--graph-node-container-fill)',
          'border-color': 'var(--graph-node-container-border)',
          'shape': 'round-rectangle',
        },
      },
      {
        selector: 'node[level="external"]',
        style: {
          'background-color': 'var(--graph-node-external-fill)',
          'border-color': 'var(--graph-node-external-border)',
          'shape': 'round-rectangle',
        },
      },
      {
        selector: 'node[iconUrl]',
        style: {
          'background-image': 'data(iconUrl)',
          'background-width': '80%',
          'background-height': '80%',
          'background-fit': 'contain',
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 'var(--graph-edge-width)',
          'line-color': 'var(--graph-edge-stroke)',
          'target-arrow-color': 'var(--graph-edge-stroke)',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'arrow-scale': 0.8,
        },
      },
    ];
  }
}
