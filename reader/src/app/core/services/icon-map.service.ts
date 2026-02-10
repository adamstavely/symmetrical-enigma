import { Injectable } from '@angular/core';

/**
 * Maps vendor/type to asset paths for external/cloud nodes.
 * Bundle AWS (or other) icons under assets/icons/aws/; fallback when no match.
 */
@Injectable({ providedIn: 'root' })
export class IconMapService {
  /** vendor or type -> path relative to assets (e.g. icons/aws/Amazon-S3.svg) */
  private readonly map: Record<string, string> = {
    AWS: 'icons/aws/aws.svg',
    S3: 'icons/aws/Amazon-S3.svg',
    Lambda: 'icons/aws/AWS-Lambda.svg',
    RDS: 'icons/aws/Amazon-RDS.svg',
    EC2: 'icons/aws/Amazon-EC2.svg',
    'API Gateway': 'icons/aws/Amazon-API-Gateway.svg',
  };

  getIconUrl(vendor?: string, type?: string): string | null {
    const key = (type ?? vendor ?? '').trim();
    if (!key) return null;
    const path = this.map[key] ?? this.map[vendor ?? ''] ?? null;
    if (!path) return null;
    return path.startsWith('http') ? path : `assets/${path}`;
  }
}
