import { Injectable, signal, computed } from '@angular/core';
import { Observable, tap, catchError, of } from 'rxjs';
import { ArchitectureApiService } from './architecture-api.service';
import type {
  EnterpriseView,
  SystemDetail,
  ContainerDetail,
  C4Level,
  ArchitectureVersion,
} from '../../models/architecture';

@Injectable({ providedIn: 'root' })
export class ArchitectureStateService {
  private readonly loading = signal(false);
  private readonly error = signal<string | null>(null);
  private readonly enterpriseView = signal<EnterpriseView | null>(null);
  private readonly systemDetail = signal<SystemDetail | null>(null);
  private readonly containerDetail = signal<ContainerDetail | null>(null);
  private readonly currentSystemId = signal<string | null>(null);
  private readonly currentContainerId = signal<string | null>(null);
  private readonly selectedVersionId = signal<string | null>(null);
  private readonly systemVersions = signal<ArchitectureVersion[]>([]);

  readonly isLoading = this.loading.asReadonly();
  readonly errorMessage = this.error.asReadonly();
  readonly enterprise = this.enterpriseView.asReadonly();
  readonly system = this.systemDetail.asReadonly();
  readonly container = this.containerDetail.asReadonly();
  readonly systemId = this.currentSystemId.asReadonly();
  readonly containerId = this.currentContainerId.asReadonly();
  readonly versionId = this.selectedVersionId.asReadonly();
  readonly versions = this.systemVersions.asReadonly();

  readonly level = computed<C4Level>(() => {
    if (this.containerDetail()) return 'container';
    if (this.systemDetail()) return 'system';
    return 'enterprise';
  });

  readonly graphData = computed(() => {
    const ent = this.enterpriseView();
    const sys = this.systemDetail();
    const cont = this.containerDetail();
    if (cont) return { nodes: cont as unknown, edges: [] };
    if (sys) {
      const nodes = [sys, ...(sys.containers || [])];
      const edges = (sys.relationships || []).map((r) => ({
        source: r.from ?? r.to,
        target: r.to ?? r.from,
        type: r.type ?? 'depends_on',
      }));
      return { nodes, edges };
    }
    if (ent) return { nodes: ent.systems, edges: ent.edges };
    return { nodes: [], edges: [] };
  });

  constructor(private api: ArchitectureApiService) {}

  loadEnterpriseView(): Observable<EnterpriseView | null> {
    this.loading.set(true);
    this.error.set(null);
    this.currentSystemId.set(null);
    this.currentContainerId.set(null);
    this.systemDetail.set(null);
    this.containerDetail.set(null);
    return this.api.getEnterpriseView().pipe(
      tap((data) => {
        this.enterpriseView.set(data);
        this.loading.set(false);
      }),
      catchError((err) => {
        this.error.set(err?.message ?? 'Failed to load enterprise view');
        this.loading.set(false);
        return of(null);
      })
    );
  }

  loadSystemDetail(systemId: string, versionId?: string): Observable<SystemDetail | null> {
    this.loading.set(true);
    this.error.set(null);
    this.currentSystemId.set(systemId);
    this.selectedVersionId.set(versionId ?? null);
    this.currentContainerId.set(null);
    this.containerDetail.set(null);
    return this.api.getSystemDetail(systemId, versionId).pipe(
      tap((data) => {
        this.systemDetail.set(data ?? null);
        this.loading.set(false);
      }),
      catchError((err) => {
        this.error.set(err?.message ?? 'Failed to load system');
        this.loading.set(false);
        return of(null);
      })
    );
  }

  loadSystemVersions(systemId: string): void {
    this.api.getSystemVersions(systemId).subscribe({
      next: (res) => this.systemVersions.set(res.versions ?? []),
      error: () => this.systemVersions.set([]),
    });
  }

  loadContainerDetail(systemId: string, containerId: string): Observable<ContainerDetail | null> {
    this.loading.set(true);
    this.error.set(null);
    this.currentSystemId.set(systemId);
    this.currentContainerId.set(containerId);
    return this.api.getContainerDetail(systemId, containerId).pipe(
      tap((data) => {
        this.containerDetail.set(data ?? null);
        this.loading.set(false);
      }),
      catchError((err) => {
        this.error.set(err?.message ?? 'Failed to load container');
        this.loading.set(false);
        return of(null);
      })
    );
  }

  clearSelection(): void {
    this.currentSystemId.set(null);
    this.currentContainerId.set(null);
    this.selectedVersionId.set(null);
    this.systemVersions.set([]);
    this.systemDetail.set(null);
    this.containerDetail.set(null);
  }

  clearError(): void {
    this.error.set(null);
  }
}
