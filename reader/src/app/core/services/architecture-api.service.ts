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
} from '../../models/architecture';

@Injectable({ providedIn: 'root' })
export class ArchitectureApiService {
  private readonly base = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getEnterpriseView(): Observable<EnterpriseView> {
    return this.http.get<EnterpriseView>(`${this.base}/enterprise`);
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

  getSystems(group?: string, skip = 0, limit = 50): Observable<{ systems: unknown[] }> {
    let params = new HttpParams().set('skip', String(skip)).set('limit', String(limit));
    if (group) params = params.set('group', group);
    return this.http.get<{ systems: unknown[] }>(`${this.base}/systems`, { params });
  }

  getGroups(): Observable<string[]> {
    return this.http.get<{ groups: string[] }>(`${this.base}/groups`).pipe(
      map((r) => r.groups ?? [])
    );
  }

  search(query: string, filters?: SearchFilters, limit = 20): Observable<SearchResultItem[]> {
    return this.http.post<{ results: SearchResultItem[] }>(`${this.base}/search`, { query, filters, limit }).pipe(
      map((r) => r.results ?? [])
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
}
