import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import type {
  EnterpriseView,
  SystemDetail,
  ContainerDetail,
  SearchResultItem,
  SearchFilters,
  DependenciesResponse,
  ArchitectureVersion,
  VersionDiff,
  DriftAlert,
  DriftAlertsResponse,
  AnalyzeResponse,
} from '../../models/architecture';

@Injectable({ providedIn: 'root' })
export class ArchitectureApiService {
  private readonly base = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getEnterpriseView(technology?: string): Observable<EnterpriseView> {
    const params = technology ? new HttpParams().set('technology', technology) : undefined;
    return this.http.get<EnterpriseView>(`${this.base}/enterprise`, params ? { params } : {});
  }

  getSystemDetail(systemId: string, versionId?: string): Observable<SystemDetail | null> {
    let params = new HttpParams();
    if (versionId) params = params.set('version', versionId);
    return this.http.get<SystemDetail | null>(
      `${this.base}/systems/${encodeURIComponent(systemId)}`,
      params.keys().length ? { params } : {}
    );
  }

  getSystemVersions(systemId: string, limit = 20): Observable<{ system_id: string; versions: ArchitectureVersion[] }> {
    const params = new HttpParams().set('limit', String(limit));
    return this.http.get<{ system_id: string; versions: ArchitectureVersion[] }>(
      `${this.base}/systems/${encodeURIComponent(systemId)}/versions`,
      { params }
    );
  }

  getContainerDetail(systemId: string, containerId: string): Observable<ContainerDetail | null> {
    return this.http.get<ContainerDetail | null>(
      `${this.base}/systems/${encodeURIComponent(systemId)}/containers/${encodeURIComponent(containerId)}`
    );
  }

  getSystems(
    group?: string,
    technology?: string,
    skip = 0,
    limit = 50
  ): Observable<{ systems: unknown[]; total: number }> {
    let params = new HttpParams().set('skip', String(skip)).set('limit', String(limit));
    if (group) params = params.set('group', group);
    if (technology) params = params.set('technology', technology);
    return this.http.get<{ systems: unknown[]; total: number }>(`${this.base}/systems`, { params });
  }

  getTechnologies(): Observable<string[]> {
    return this.http.get<{ technologies: string[] }>(`${this.base}/technologies`).pipe(
      map((r) => r.technologies ?? [])
    );
  }

  getTechnologyInventory(): Observable<Array<{ technology: string; system_ids: string[] }>> {
    return this.http
      .get<{ technologies: string[]; inventory: Array<{ technology: string; system_ids: string[] }> }>(
        `${this.base}/technologies`,
        { params: { inventory: 'true' } }
      )
      .pipe(map((r) => r.inventory ?? []));
  }

  getGroups(): Observable<string[]> {
    return this.http.get<{ groups: string[] }>(`${this.base}/groups`).pipe(
      map((r) => r.groups ?? [])
    );
  }

  search(query: string, filters?: SearchFilters, limit = 20): Observable<SearchResultItem[]> {
    const body: { query: string; filters?: SearchFilters; limit?: number } = { query, limit };
    if (filters && (filters.group || filters.technology)) body.filters = filters;
    return this.http.post<{ results: SearchResultItem[] }>(`${this.base}/search`, body).pipe(
      map((r) => r.results ?? [])
    );
  }

  getVersionDiff(
    systemId: string,
    fromVersionId: string,
    toVersionId: string
  ): Observable<VersionDiff | null> {
    const params = new HttpParams()
      .set('from', fromVersionId)
      .set('to', toVersionId);
    return this.http.get<VersionDiff | null>(
      `${this.base}/systems/${encodeURIComponent(systemId)}/versions/diff`,
      { params }
    );
  }

  getDependencies(
    nodeId: string,
    direction: 'upstream' | 'downstream' | 'both' = 'both',
    depth = 2
  ): Observable<DependenciesResponse> {
    const params = new HttpParams()
      .set('direction', direction)
      .set('depth', String(depth));
    return this.http.get<DependenciesResponse>(
      `${this.base}/dependencies/${encodeURIComponent(nodeId)}`,
      { params }
    );
  }

  getDriftAlerts(params?: { min_severity?: string; limit?: number }): Observable<DriftAlert[]> {
    let httpParams = new HttpParams().set('limit', String(params?.limit ?? 100));
    if (params?.min_severity) {
      httpParams = httpParams.set('min_severity', params.min_severity);
    }
    return this.http
      .get<DriftAlertsResponse>(`${this.base}/drift`, { params: httpParams })
      .pipe(map((r) => r.alerts ?? []));
  }

  analyzeRepository(repositoryUrl: string): Observable<AnalyzeResponse> {
    return this.http.post<AnalyzeResponse>(`${this.base}/analyze`, {
      repository_url: repositoryUrl,
    });
  }
}
