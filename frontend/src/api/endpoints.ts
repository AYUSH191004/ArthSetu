import { api } from "@/lib/api";
import type {
  AnalyticsSummary,
  AuditEntry,
  BusinessProfile,
  BusinessSearchItem,
  DashboardResponse,
  DistrictRow,
  HealthResponse,
  IngestionReport,
  LoginResponse,
  Page,
  ProcessPendingResult,
  ReviewCaseItem,
  ReviewDecisionResponse,
  Role,
  SourceSystem,
  StatusResult,
  TrendPoint,
  User,
} from "@/types/api";

export const authApi = {
  login: (username: string, password: string) => {
    const form = new URLSearchParams({ username, password });
    return api
      .post<LoginResponse>("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      .then((r) => r.data);
  },
  me: () => api.get<User>("/auth/me").then((r) => r.data),
  changePassword: (current_password: string, new_password: string) =>
    api
      .post("/auth/change-password", { current_password, new_password })
      .then(() => undefined),

  listUsers: () => api.get<User[]>("/auth/users").then((r) => r.data),
  createUser: (body: {
    username: string;
    full_name: string;
    email?: string;
    role: Role;
    password: string;
  }) => api.post<User>("/auth/users", body).then((r) => r.data),
  updateUser: (
    id: string,
    body: Partial<{
      full_name: string;
      email: string | null;
      role: Role;
      is_active: boolean;
    }>,
  ) => api.patch<User>(`/auth/users/${id}`, body).then((r) => r.data),
  resetPassword: (id: string, new_password: string) =>
    api
      .post<User>(`/auth/users/${id}/reset-password`, { new_password })
      .then((r) => r.data),
};

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

export const ingestApi = {
  sourceSystems: () =>
    api.get<SourceSystem[]>("/ingest/source-systems").then((r) => r.data),
  pending: () =>
    api.get<{ pending: number }>("/ingest/pending").then((r) => r.data.pending),
  downloadTemplate: async () => {
    const res = await api.get<Blob>("/ingest/template", { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = "arthsetu_import_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  },
  uploadCsv: (file: File, sourceSystemCode: string, process: boolean) => {
    const form = new FormData();
    form.append("file", file);
    form.append("source_system_code", sourceSystemCode);
    form.append("process", String(process));
    return api
      .post<IngestionReport>("/ingest/csv", form)
      .then((r) => r.data);
  },
  processPending: () =>
    api
      .post<ProcessPendingResult>("/ingest/process-pending")
      .then((r) => r.data),
};
