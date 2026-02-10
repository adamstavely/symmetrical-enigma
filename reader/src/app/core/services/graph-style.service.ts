import { Injectable } from '@angular/core';
import type { StylesheetStyle } from 'cytoscape';

/**
 * Builds Cytoscape stylesheet. Uses explicit hex colors so labels and nodes
 * are readable on the dark graph background (Cytoscape may not resolve CSS variables).
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
          'color': '#f0f6fc',
          'font-size': 14,
          'text-margin-y': 6,
          'width': 160,
          'height': 72,
          'background-color': '#1a3a5a',
          'border-color': '#3d6b9e',
          'border-width': 2,
          'border-opacity': 1,
          'shape': 'round-rectangle',
        },
      },
      {
        selector: 'node[level="system"]',
        style: {
          'background-color': '#1a3a5a',
          'border-color': '#3d6b9e',
          'shape': 'round-rectangle',
        },
      },
      {
        selector: 'node[level="container"]',
        style: {
          'background-color': '#243b4f',
          'border-color': '#4a6b85',
          'shape': 'round-rectangle',
        },
      },
      {
        selector: 'node[level="component"]',
        style: {
          'background-color': '#2d4a3e',
          'border-color': '#4a7c59',
          'shape': 'round-rectangle',
          'width': 140,
          'height': 56,
        },
      },
      {
        selector: 'node[level="external"]',
        style: {
          'background-color': '#21262d',
          'border-color': '#d4a84b',
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
          'width': 2.5,
          'line-color': '#4a6b85',
          'target-arrow-color': '#4a6b85',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'arrow-scale': 0.8,
        },
      },
    ];
  }
}
