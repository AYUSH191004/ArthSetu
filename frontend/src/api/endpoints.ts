import { api } from "@/lib/api";
import type {
  AnalyticsSummary,
  AuditEntry,
  BusinessProfile,
  BusinessSearchItem,
  DashboardResponse,
  DistrictRow,
  HealthResponse,
  Page,
  ReviewCaseItem,
  ReviewDecisionResponse,
  StatusResult,
  TrendPoint,
} from "@/types/api";

export const healthApi = {
  get: () => api.get<HealthResponse>("/health").then((r) => r.data),
};

export const dashboardApi = {
  get: () => api.get<DashboardResponse>("/dashboard").then((r) => r.data),
};

export const analyticsApi = {
  summary: () =>
    api.get<AnalyticsSummary>("/analytics/summary").then((r) => r.data),
  trends: () => api.get<TrendPoint[]>("/analytics/trends").then((r) => r.data),
  districts: () =>
    api.get<DistrictRow[]>("/analytics/districts").then((r) => r.data),
};

export interface BusinessSearchParams {
  q?: string;
  status?: string;
  district?: string;
  limit?: number;
  offset?: number;
}

export const businessApi = {
  search: (params: BusinessSearchParams) =>
    api
      .get<Page<BusinessSearchItem>>("/business/search", { params })
      .then((r) => r.data),
  profile: (ubid: string) =>
    api.get<BusinessProfile>(`/business/${encodeURIComponent(ubid)}`).then((r) => r.data),
};

export interface ReviewListParams {
  status?: string;
  limit?: number;
  offset?: number;
}

export const reviewApi = {
  list: (params: ReviewListParams) =>
    api.get<Page<ReviewCaseItem>>("/reviews", { params }).then((r) => r.data),
  approve: (id: string) =>
    api
      .post<ReviewDecisionResponse>(`/reviews/${id}/approve`)
      .then((r) => r.data),
  reject: (id: string) =>
    api.post<ReviewDecisionResponse>(`/reviews/${id}/reject`).then((r) => r.data),
};

export const statusApi = {
  recompute: (ubid: string) =>
    api.get<StatusResult>(`/status/${encodeURIComponent(ubid)}`).then((r) => r.data),
  runAll: () => api.post("/status/run-all").then((r) => r.data),
};

export interface AuditParams {
  entity_type?: string;
  entity_id?: string;
  action?: string;
  limit?: number;
  offset?: number;
}

export const auditApi = {
  list: (params: AuditParams) =>
    api.get<Page<AuditEntry>>("/audit", { params }).then((r) => r.data),
};
