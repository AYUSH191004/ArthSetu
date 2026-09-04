// Mirrors Docs/API_CONTRACT.md — keep in sync with the backend.

export type Role = "admin" | "reviewer" | "viewer";

export interface User {
  id: string;
  username: string;
  full_name: string;
  email: string | null;
  role: Role;
  is_active: boolean;
  created_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  database: string;
}

export interface DashboardResponse {
  total_businesses: number;
  active: number;
  dormant: number;
  closed: number;
  unknown: number;
  pending_reviews: number;
  total_links: number;
  auto_match_rate: number;
}

export interface AnalyticsSummary {
  total_businesses: number;
  active: number;
  dormant: number;
  closed: number;
  unknown: number;
}

export interface TrendPoint {
  month: string;
  events: number;
}

export interface DistrictRow {
  district: string;
  total: number;
  active: number;
  dormant: number;
  closed: number;
  unknown: number;
}

export interface Page<T> {
  total: number;
  limit: number;
  offset: number;
  items: T[];
}

export interface BusinessSearchItem {
  ubid: string;
  business_name: string;
  status: string;
  district: string | null;
  pin_code: string | null;
  pan: string | null;
  gstin: string | null;
}

export interface LinkedRecord {
  link_id: string;
  source_record_id: string;
  source_system: string | null;
  department: string | null;
  external_id: string | null;
  extracted_name: string | null;
  extracted_address: string | null;
  extracted_pin: string | null;
  confidence: number | null;
  decision: string | null;
}

export interface MatchingEvidence {
  signal: string;
  value: string;
}

export interface TimelineEvent {
  date: string | null;
  event: string;
  score: number | null;
}

export interface StatusHistoryPoint {
  date: string;
  status: string;
  confidence: number | null;
}

export interface BusinessProfile {
  id: string;
  ubid: string;
  business_name: string;
  status: string;
  pan: string | null;
  gstin: string | null;
  address: string | null;
  pin_code: string | null;
  district: string | null;
  sector: string | null;
  linked_records_count: number;
  linked_records: LinkedRecord[];
  matching_evidence: MatchingEvidence[];
  timeline: TimelineEvent[];
  status_history: StatusHistoryPoint[];
}

export interface ReviewEvidence {
  candidate_entity_id?: string;
  candidate_name?: string;
  confidence?: number;
  reasons?: string[];
}

export interface ReviewCaseItem {
  review_id: string;
  source_record_id: string;
  candidate_entity_id: string | null;
  candidate_name: string | null;
  candidate_ubid: string | null;
  source_system: string | null;
  extracted_name: string | null;
  status: string;
  confidence: number | null;
  evidence: ReviewEvidence | null;
  notes: string | null;
  reviewer_id: string | null;
  created_at: string | null;
  decided_at: string | null;
}

export interface ReviewDecisionResponse {
  message: string;
  review_id: string;
  status: string;
  linked_entity_id: string | null;
  link_id: string | null;
}

export interface StatusResult {
  business_entity_id: string;
  ubid_code: string;
  status: string;
  confidence: number;
  reasons: string[];
}

export interface MatchingResult {
  decision: string;
  confidence: number;
  business_entity_id: string | null;
  reasons: string[];
}

export interface AuditEntry {
  id: string;
  actor_type: string;
  actor_id: string | null;
  entity_type: string | null;
  entity_id: string | null;
  action: string | null;
  before_state: unknown;
  after_state: unknown;
  created_at: string | null;
}
