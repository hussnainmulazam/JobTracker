/**
 * lib/api.ts
 * ~~~~~~~~~~
 * Type-safe HTTP client for the AI Candidate Screening Copilot (Recruiting SaaS).
 * Connects directly to FastAPI backend with JWT bearer authentication.
 */

const rawBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// Clean trailing slashes reliably to avoid URL concatenation bugs
export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, "");

export function getFullApiUrl(endpoint: string): string {
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return endpoint;
  }
  const cleanPath = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${API_BASE_URL}${cleanPath}`;
}

/**
 * Low-level backend fetch wrapper ensuring correct base URL and ngrok bypass headers.
 */
export async function backendFetch(
  endpoint: string,
  init: RequestInit = {}
): Promise<Response> {
  const url = getFullApiUrl(endpoint);
  const headers = new Headers(init.headers);
  headers.set("ngrok-skip-browser-warning", "true");
  return fetch(url, {
    ...init,
    headers,
  });
}

const TOKEN_STORAGE_KEY = "job_tracker_token";

// ── Auth Token Storage ────────────────────────────────────────────────────────

export function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (stored) return stored;

    const urlParams = new URLSearchParams(window.location.search);
    const queryToken = urlParams.get("token");
    if (queryToken) {
      localStorage.setItem(TOKEN_STORAGE_KEY, queryToken);
      window.dispatchEvent(new Event("auth-change"));
      return queryToken;
    }

    return null;
  } catch {
    return null;
  }
}

export function setAuthToken(token: string): void {
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
      window.dispatchEvent(new Event("auth-change"));
    } catch (e) {
      console.error("Failed to persist auth token:", e);
    }
  }
}

export function removeAuthToken(): void {
  if (typeof window !== "undefined") {
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      window.dispatchEvent(new Event("auth-change"));
    } catch (e) {
      console.error("Failed to remove auth token:", e);
    }
  }
}

// ── Types ───────────────────────────────────────────────────────────────────

export type JobOpeningStatus = "draft" | "active" | "paused" | "closed";

export type CandidateStage =
  | "applied"
  | "screening"
  | "shortlisted"
  | "contacted"
  | "scheduled"
  | "interview"
  | "interviewed"
  | "offer"
  | "rejected";

export interface JobOpening {
  id: string;
  user_id: string;
  title: string;
  description: string;
  required_skills: string[];
  years_of_experience?: number | null;
  nice_to_haves?: string[];
  status: JobOpeningStatus;
  pass_mark?: number;
  google_sheet_id?: string | null;
  google_sheet_url?: string | null;
  created_at: string;
  updated_at: string;
  candidates_count?: number;
}

export interface PaginatedJobOpenings {
  items: JobOpening[];
  total: number;
  skip: number;
  limit: number;
}

export interface Scorecard {
  id: string;
  user_id: string;
  candidate_id: string;
  rating: number; // 1-5
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedScorecards {
  items: Scorecard[];
  total: number;
}

export interface ExtractedFieldMeta {
  value?: string | null;
  confidence: number;
  source: string;
}

export interface ExtractedCandidateData {
  name?: string | null;
  email?: string | null;
  secondary_emails?: string[];
  phone?: string | null;
  secondary_phones?: string[];
  address?: string | null;
  current_title?: string | null;
  years_of_experience?: number | null;
  top_skills?: string[];
  education?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  kaggle_url?: string | null;
  portfolio_url?: string | null;
  other_links?: string[];
}

export interface CandidateDuplicateInfo {
  is_duplicate: boolean;
  matched_by?: "email" | "phone" | null;
  existing_candidate_id?: string | null;
  existing_candidate_name?: string | null;
  existing_candidate_email?: string | null;
  existing_opening_id?: string | null;
  existing_opening_title?: string | null;
  existing_stage?: string | null;
  existing_score?: number | null;
}

export interface CandidateExtractionPreviewResponse {
  file_name?: string | null;
  file_url?: string | null;
  cv_text: string;
  opening_id: string;
  extracted_data: ExtractedCandidateData;
  field_metadata: Record<string, ExtractedFieldMeta>;
  duplicate_info: CandidateDuplicateInfo;
  low_confidence_fields: string[];
  missing_fields: string[];
}

export interface CandidateConfirmPayload {
  opening_id: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  current_title?: string | null;
  years_of_experience?: number | null;
  top_skills?: string[];
  education?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  kaggle_url?: string | null;
  portfolio_url?: string | null;
  other_links?: string[];
  cv_text: string;
  cv_file_url?: string | null;
  field_metadata?: Record<string, ExtractedFieldMeta>;
  extracted_data?: Record<string, any>;
  auto_screen?: boolean;
  action?: "create" | "merge" | "skip";
  merge_candidate_id?: string | null;
}

export interface CandidateLinkRead {
  id: string;
  candidate_id: string;
  link_type: "github" | "linkedin" | "kaggle" | "portfolio" | "other" | string;
  url: string;
  is_verified?: boolean | null;
  confidence: number;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface ExtractedFieldMeta {
  value?: string | null;
  confidence: number;
  source: string;
}

export interface CandidateExtractedDetails {
  candidate_id: string;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  kaggle_url?: string | null;
  other_links: string[];
  field_metadata: Record<string, ExtractedFieldMeta>;
  links_verified: Record<string, boolean | null>;
}

export interface GoogleSheetSyncResponse {
  spreadsheet_id: string;
  spreadsheet_url: string;
  total_candidates_synced: number;
  rows_updated: number;
  rows_appended: number;
  synced_at: string;
}

export interface Candidate {
  id: string;
  user_id: string;
  opening_id: string;
  name: string;
  email: string;
  phone?: string | null;
  address?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  kaggle_url?: string | null;
  extracted_data?: Record<string, { value: string | null; confidence: number; source: string }> | null;
  cv_text: string;
  cv_file_url?: string | null;
  score?: number | null;
  matched_skills: string[];
  missing_skills: string[];
  red_flags: string[];
  summary?: string | null;
  stage: CandidateStage;
  review_status?: "pending" | "approved" | "rejected";
  recommendation?: "Recommended" | "Borderline" | "Not recommended" | "Unscored" | null;
  review_decision_at?: string | null;
  auto_reply_sent?: boolean;
  auto_reply_status?: string | null;
  auto_reply_error?: string | null;
  auto_reply_sent_at?: string | null;
  created_at: string;
  updated_at: string;
  whatsapp_opt_in?: boolean;
  whatsapp_opt_in_at?: string | null;
  last_inbound_whatsapp_at?: string | null;
  opening_title?: string;
  scorecards?: Scorecard[];
  links?: CandidateLinkRead[];
}

export interface PaginatedCandidates {
  items: Candidate[];
  total: number;
  skip: number;
  limit: number;
}

export interface CandidateScreenResult {
  candidate_id: string;
  candidate_name: string;
  score: number;
  matched_skills: string[];
  missing_skills: string[];
  red_flags: string[];
  summary: string;
  recommendation?: string;
  interview_focus_areas?: string[];
  rank?: number;
  stage?: CandidateStage;
  model_used?: string;
  latency_seconds?: number;
}

export interface BulkScoreResponse {
  opening_id: string;
  opening_title: string;
  total_candidates: number;
  ranked_candidates: CandidateScreenResult[];
}

export interface FunnelStageItem {
  stage: string;
  label: string;
  count: number;
  percentage: number;
}

export interface UpcomingInterviewItem {
  id: string;
  title: string;
  candidate_name: string;
  candidate_email: string;
  opening_title?: string | null;
  start_time: string;
  end_time: string;
  meet_link?: string | null;
  status: string;
}

export interface AwaitingReplyThreadItem {
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  opening_title?: string | null;
  last_message: string;
  received_at: string;
  hours_ago: number;
}

export interface DashboardStats {
  total_openings: number;
  active_openings: number;
  total_candidates: number;
  screened_candidates: number;
  shortlisted_candidates: number;
  average_score: number | null;
  new_cvs_today: number;
  pending_reviews: number;
  messages_awaiting_reply: number;
  interviews_this_week: number;
  interviews_today?: number;
  time_to_shortlist_hours: number | null;
  candidates_trend_pct?: number | null;
  candidates_this_week?: number;
  openings_trend_pct?: number | null;
  interviews_trend_pct?: number | null;
  stage_breakdown: Record<CandidateStage, number>;
  funnel_by_stage: FunnelStageItem[];
  applications_timeline?: Array<{
    date: string;
    label: string;
    day: string;
    count: number;
  }>;
  recent_candidates: Array<{
    id: string;
    name: string;
    email: string;
    opening_title?: string;
    stage: CandidateStage;
    score: number | null;
    created_at: string;
  }>;
  recent_activity?: Array<{
    id: string;
    action: string;
    candidate_id?: string | null;
    candidate_name?: string | null;
    opening_title?: string | null;
    from_stage?: string | null;
    to_stage?: string | null;
    details?: string | null;
    created_at: string;
  }>;
  openings_summary: Array<{
    id: string;
    title: string;
    status: JobOpeningStatus;
    candidates_count?: number;
    total_candidates?: number;
    average_score: number | null;
  }>;
  upcoming_interviews: UpcomingInterviewItem[];
  awaiting_reply_threads: AwaitingReplyThreadItem[];
}

export interface AuditLog {
  id: string;
  user_id: string;
  candidate_id?: string | null;
  candidate_name?: string | null;
  opening_id?: string | null;
  opening_title?: string | null;
  action: string;
  from_stage?: string | null;
  to_stage?: string | null;
  details?: string | null;
  created_at: string;
}

export interface PaginatedAuditLogs {
  items: AuditLog[];
  total: number;
}

export interface NotificationItem {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: string;
  link?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  unread_count: number;
}

export interface SearchResultItem {
  id: string;
  type: "candidate" | "opening" | "action";
  title: string;
  subtitle: string;
  link: string;
  score?: number | null;
  stage_or_status?: string | null;
  matched_skills: string[];
}

export interface SearchResponse {
  query: string;
  candidates: SearchResultItem[];
  openings: SearchResultItem[];
  quick_actions: SearchResultItem[];
  total_results: number;
}

export interface WhatsAppConversationSummary {
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string | null;
  opening_id?: string | null;
  opening_title?: string | null;
  candidate_stage: string;
  candidate_score?: number | null;
  whatsapp_opt_in: boolean;
  last_message_body?: string | null;
  last_message_direction?: string | null;
  last_message_status?: string | null;
  last_message_at?: string | null;
  total_messages: number;
  awaiting_reply: boolean;
  care_window_open: boolean;
  care_window_expires_at?: string | null;
  seconds_remaining?: number | null;
}

export interface WhatsAppConversationsResponse {
  conversations: WhatsAppConversationSummary[];
  total_conversations: number;
  awaiting_reply_count: number;
}

// ── Custom API Error Class ──────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

// ── Core Fetch Wrapper ──────────────────────────────────────────────────────

export interface ApiFetchOptions extends RequestInit {
  token?: string | null;
  skipAuth?: boolean;
}

export async function apiFetch<T>(
  endpoint: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { token, skipAuth = false, headers, ...customConfig } = options;

  const reqHeaders = new Headers(headers);
  // Ensure ngrok browser warning skip header is present on every request
  reqHeaders.set("ngrok-skip-browser-warning", "true");

  if (!skipAuth) {
    const activeToken = token ?? getAuthToken();
    if (activeToken) {
      reqHeaders.set("Authorization", `Bearer ${activeToken}`);
    }
  }

  if (
    customConfig.body &&
    typeof customConfig.body === "string" &&
    !reqHeaders.has("Content-Type")
  ) {
    reqHeaders.set("Content-Type", "application/json");
  }

  const response = await backendFetch(endpoint, {
    ...customConfig,
    headers: reqHeaders,
  });

  if (response.status === 401) {
    removeAuthToken();

    if (typeof window !== "undefined") {
      try {
        fetch("/api/auth/logout", { method: "POST" }).catch(() => {});
        document.cookie = "auth_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      } catch {}

      const currentPath = window.location.pathname;
      if (!currentPath.startsWith("/login") && !currentPath.startsWith("/register")) {
        // Use replace to avoid browser back history loop and clear ongoing polling
        window.location.replace(`/login?redirect=${encodeURIComponent(currentPath)}`);
      }
    }

    throw new ApiError(401, "Session expired or invalid credentials.", null);
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    let errorData: unknown = null;

    try {
      errorData = await response.json();
      if (typeof errorData === "object" && errorData !== null) {
        const errorRecord = errorData as Record<string, unknown>;
        if (typeof errorRecord.detail === "string") {
          errorDetail = errorRecord.detail;
        } else if (Array.isArray(errorRecord.detail)) {
          errorDetail = errorRecord.detail
            .map((err: { msg?: string; loc?: (string | number)[] }) => {
              const field = err.loc ? err.loc.slice(-1)[0] : "field";
              return `${field}: ${err.msg || "Invalid value"}`;
            })
            .join(", ");
        } else if (typeof errorRecord.message === "string") {
          errorDetail = errorRecord.message;
        }
      }
    } catch {
      // Body not JSON
    }

    throw new ApiError(response.status, errorDetail, errorData);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json();
}

// ── Generic API Methods ─────────────────────────────────────────────────────

export const api = {
  get: <T>(endpoint: string, options?: ApiFetchOptions) =>
    apiFetch<T>(endpoint, { ...options, method: "GET" }),

  post: <T>(endpoint: string, data?: unknown, options?: ApiFetchOptions) =>
    apiFetch<T>(endpoint, {
      ...options,
      method: "POST",
      body:
        data instanceof FormData
          ? data
          : data
          ? JSON.stringify(data)
          : undefined,
    }),

  patch: <T>(endpoint: string, data?: unknown, options?: ApiFetchOptions) =>
    apiFetch<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T>(endpoint: string, data?: unknown, options?: ApiFetchOptions) =>
    apiFetch<T>(endpoint, {
      ...options,
      method: "PUT",
      body:
        data instanceof FormData
          ? data
          : data
          ? JSON.stringify(data)
          : undefined,
    }),

  delete: <T>(endpoint: string, options?: ApiFetchOptions) =>
    apiFetch<T>(endpoint, { ...options, method: "DELETE" }),
};

export interface GoogleAuthPayload {
  code: string;
  redirect_uri?: string;
}

export interface GoogleAuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    created_at: string;
  };
  setup_completed: boolean;
  is_new_user: boolean;
}

export const authApi = {
  getGoogleAuthUrl: (redirectUri?: string) => {
    const params = redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : "";
    return api.get<{ url: string }>(`/api/v1/auth/google/url${params}`, { skipAuth: true });
  },
  authenticateGoogle: (payload: GoogleAuthPayload) =>
    api.post<GoogleAuthResponse>("/api/v1/auth/google", payload, { skipAuth: true }),
};

// ── Domain API Services ─────────────────────────────────────────────────────

export interface MatchProgressStatus {
  opening_id: string;
  status: "idle" | "in_progress" | "completed" | "failed";
  total_candidates: number;
  processed_candidates: number;
  matched_candidates: number;
  progress_percent: number;
  errors: string[];
  started_at?: string | null;
  completed_at?: string | null;
}

export const jobOpeningsApi = {
  list: (status?: string, limit: number = 50, skip: number = 0) => {
    const params = new URLSearchParams({ limit: String(limit), skip: String(skip) });
    if (status) params.append("status", status);
    return api.get<PaginatedJobOpenings>(`/api/v1/job-openings?${params.toString()}`);
  },

  get: (id: string) => api.get<JobOpening>(`/api/v1/job-openings/${id}`),

  create: (data: {
    title: string;
    description: string;
    required_skills: string[];
    status?: JobOpeningStatus;
    pass_mark?: number;
  }) => api.post<JobOpening>("/api/v1/job-openings", data),

  update: (
    id: string,
    data: Partial<{
      title: string;
      description: string;
      required_skills: string[];
      status: JobOpeningStatus;
      pass_mark: number;
    }>
  ) => api.patch<JobOpening>(`/api/v1/job-openings/${id}`, data),

  delete: (id: string) => api.delete<void>(`/api/v1/job-openings/${id}`),

  bulkScore: (id: string) =>
    api.post<BulkScoreResponse>(`/api/v1/job-openings/${id}/bulk-score`),

  match: (id: string, rerun: boolean = false) =>
    api.post<MatchProgressStatus>(`/api/v1/job-openings/${id}/match?rerun=${rerun}`),

  getMatchStatus: (id: string) =>
    api.get<MatchProgressStatus>(`/api/v1/job-openings/${id}/match/status`),

  generateQuestions: (id: string, count: number = 5) =>
    api.post<{ questions: string[] }>(
      `/api/v1/job-openings/${id}/screening-questions?count=${count}`
    ),

  getShortlistExportUrl: (id: string, minScore?: number) => {
    const params = new URLSearchParams();
    if (minScore !== undefined) params.append("min_score", String(minScore));
    const token = getAuthToken();
    return `${API_BASE_URL}/api/v1/job-openings/${id}/shortlist/export?${params.toString()}`;
  },

  syncGoogleSheet: (id: string) =>
    api.post<GoogleSheetSyncResponse>(`/api/v1/job-openings/${id}/sync-google-sheet`),

  extractAll: (id: string, verifyUrls: boolean = true) =>
    api.post<{ opening_id: string; candidates_processed: number; results: CandidateExtractedDetails[] }>(
      `/api/v1/job-openings/${id}/extract-all?verify_urls=${verifyUrls}`
    ),
};

export const candidatesApi = {
  list: (params?: {
    opening_id?: string;
    stage?: CandidateStage;
    limit?: number;
    skip?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.opening_id) searchParams.append("opening_id", params.opening_id);
    if (params?.stage) searchParams.append("stage", params.stage);
    if (params?.limit) searchParams.append("limit", String(params.limit));
    if (params?.skip) searchParams.append("skip", String(params.skip));
    return api.get<PaginatedCandidates>(`/api/v1/candidates?${searchParams.toString()}`);
  },

  get: (id: string) => api.get<Candidate>(`/api/v1/candidates/${id}`),

  create: (data: {
    opening_id: string;
    name: string;
    email: string;
    cv_text: string;
  }) => api.post<Candidate>("/api/v1/candidates", data),

  extractCv: (formData: FormData) =>
    api.post<CandidateExtractionPreviewResponse>("/api/v1/candidates/extract-cv", formData),

  extractText: (data: { opening_id: string; cv_text: string }) =>
    api.post<CandidateExtractionPreviewResponse>("/api/v1/candidates/extract-text", data),

  confirmExtracted: (data: CandidateConfirmPayload) =>
    api.post<Candidate>("/api/v1/candidates/confirm-extracted", data),

  uploadPdf: (formData: FormData) =>
    api.post<Candidate>("/api/v1/candidates/upload", formData),

  updatePdf: (id: string, formData: FormData) =>
    api.put<Candidate>(`/api/v1/candidates/${id}/upload-cv`, formData),

  update: (
    id: string,
    data: Partial<{
      name: string;
      email: string;
      phone: string | null;
      address: string | null;
      github_url: string | null;
      linkedin_url: string | null;
      portfolio_url: string | null;
      kaggle_url: string | null;
      cv_text: string;
      stage: CandidateStage;
      score: number | null;
    }>
  ) => api.patch<Candidate>(`/api/v1/candidates/${id}`, data),

  extractDetails: (id: string, verifyUrls: boolean = true) =>
    api.post<CandidateExtractedDetails>(`/api/v1/candidates/${id}/extract-details?verify_urls=${verifyUrls}`),

  getLinks: (id: string) =>
    api.get<CandidateLinkRead[]>(`/api/v1/candidates/${id}/links`),

  updateStage: (id: string, stage: CandidateStage) =>
    api.patch<Candidate>(`/api/v1/candidates/${id}/stage`, { stage }),

  score: (id: string, rerun: boolean = false) =>
    api.post<CandidateScreenResult>(
      `/api/v1/candidates/${id}/score${rerun ? "?re_run=true" : ""}`
    ),

  generateQuestions: (id: string, count: number = 5) =>
    api.post<{ candidate_id: string; candidate_name: string; questions: string[] }>(
      `/api/v1/candidates/${id}/screening-questions?count=${count}`
    ),

  bulkStage: (candidateIds: string[], stage: CandidateStage) =>
    api.post<{ updated_count: number; message: string }>("/api/v1/candidates/bulk-stage", {
      candidate_ids: candidateIds,
      stage,
    }),

  bulkDelete: (candidateIds: string[]) =>
    api.post<{ updated_count: number; message: string }>("/api/v1/candidates/bulk-delete", {
      candidate_ids: candidateIds,
    }),

  getAuditLogs: (candidateId: string) =>
    api.get<AuditLog[]>(`/api/v1/candidates/${candidateId}/audit-logs`),

  resendAutoReply: (candidateId: string) =>
    api.post<Candidate>(`/api/v1/candidates/${candidateId}/resend-auto-reply`),

  delete: (id: string) => api.delete<void>(`/api/v1/candidates/${id}`),
};

export const auditLogsApi = {
  listRecent: (params?: { opening_id?: string; limit?: number; skip?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.opening_id) searchParams.append("opening_id", params.opening_id);
    if (params?.limit) searchParams.append("limit", String(params.limit));
    if (params?.skip) searchParams.append("skip", String(params.skip));
    return api.get<PaginatedAuditLogs>(`/api/v1/candidates/audit-logs/recent?${searchParams.toString()}`);
  },
  listForCandidate: (candidateId: string) =>
    api.get<AuditLog[]>(`/api/v1/candidates/${candidateId}/audit-logs`),
};

export const notificationsApi = {
  list: (limit: number = 30) =>
    api.get<NotificationListResponse>(`/api/v1/notifications?limit=${limit}`),
  markRead: (id: string) =>
    api.patch<NotificationItem>(`/api/v1/notifications/${id}/read`, {}),
  markAllRead: () =>
    api.post<{ updated: number; message: string }>("/api/v1/notifications/read-all", {}),
};

export const searchApi = {
  search: (q: string) =>
    api.get<SearchResponse>(`/api/v1/search?q=${encodeURIComponent(q)}`),
};

export const scorecardsApi = {
  list: (candidate_id?: string) => {
    const params = candidate_id ? `?candidate_id=${candidate_id}` : "";
    return api.get<PaginatedScorecards>(`/api/v1/scorecards${params}`);
  },

  create: (data: { candidate_id: string; rating: number; notes?: string }) =>
    api.post<Scorecard>("/api/v1/scorecards", data),

  update: (id: string, data: { rating?: number; notes?: string }) =>
    api.patch<Scorecard>(`/api/v1/scorecards/${id}`, data),

  delete: (id: string) => api.delete<void>(`/api/v1/scorecards/${id}`),
};

export const dashboardApi = {
  getStats: () => api.get<DashboardStats>("/api/v1/dashboard/stats"),
};

// ── Google Integrations API ──────────────────────────────────────────────────

export interface EmailSyncItemResult {
  message_id: string;
  sender?: string | null;
  subject?: string | null;
  status: "created" | "duplicate" | "failed" | string;
  candidate_id?: string | null;
  candidate_name?: string | null;
  opening_title?: string | null;
  reason?: string | null;
}

export interface GoogleAccountStatus {
  is_connected: boolean;
  email: string | null;
  scopes: string[];
  missing_scopes?: string[];
  granted_services?: Record<string, boolean>;
  reconnect_needed?: boolean;
  reconnect_reason?: string | null;
  last_synced_at: string | null;
  last_sync_status: string;
  sync_query: string;
  sync_label: string;
  auto_reply_enabled?: boolean;
  default_opening_id?: string | null;
  default_opening_title?: string | null;
  total_emails_synced: number;
  synced_from_gmail_count?: number;
  recent_sync_results?: EmailSyncItemResult[];
}

export interface GoogleAuthUrlResponse {
  auth_url: string;
  state: string;
}

export interface GmailSyncResponse {
  status: string;
  messages_found: number;
  messages_processed: number;
  attachments_saved: number;
  candidates_created: number;
  synced_from_gmail_count?: number;
  results?: EmailSyncItemResult[];
  errors: string[];
  last_synced_at: string;
}

export interface GooglePreviewEmailRequest {
  candidate_id: string;
  template_name: string;
  custom_subject?: string;
  custom_body?: string;
  slot_link?: string;
  company_name?: string;
}

export interface GooglePreviewEmailResponse {
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  subject: string;
  body: string;
  variables: Record<string, string>;
}

export interface GoogleSendEmailRequest {
  candidate_id: string;
  subject: string;
  body: string;
  template_name?: string;
}

export interface GoogleSendEmailResponse {
  message_id: string;
  candidate_id: string;
  recipient_email: string;
  subject: string;
  status: string;
  sent_at: string;
  google_message_id?: string;
}

export const googleApi = {
  getLoginUrl: async () => {
    // 1. Try Next.js same-origin route handler first to prevent browser CORS/port issues
    try {
      const activeToken = getAuthToken();
      const headers: Record<string, string> = {};
      if (activeToken) {
        headers["Authorization"] = `Bearer ${activeToken}`;
      }
      const res = await fetch("/api/auth/google/workspace-url", {
        headers,
      });
      if (res.ok) {
        const data = await res.json();
        if (data?.auth_url) return data;
      } else {
        const errJson = await res.json().catch(() => null);
        if (errJson?.detail) {
          throw new Error(errJson.detail);
        }
      }
    } catch (routeErr: any) {
      if (routeErr?.message && !routeErr.message.includes("Failed to fetch")) {
        throw routeErr;
      }
      // Fallback to direct client fetch
    }
    return api.get<GoogleAuthUrlResponse>("/api/v1/auth/google/login");
  },
  getStatus: () => api.get<GoogleAccountStatus>("/api/v1/integrations/google/status"),
  disconnect: () => api.post<{ detail: string }>("/api/v1/integrations/google/disconnect"),
  syncGmail: (params?: { query?: string; label?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.query) searchParams.set("query", params.query);
    if (params?.label) searchParams.set("label", params.label);
    const qs = searchParams.toString();
    return api.post<GmailSyncResponse>(`/api/v1/integrations/google/sync${qs ? `?${qs}` : ""}`);
  },
  updateSettings: (data: { sync_query?: string; sync_label?: string; default_opening_id?: string | null; auto_reply_enabled?: boolean }) =>
    api.patch<GoogleAccountStatus>("/api/v1/integrations/google/settings", data),
  previewEmail: (data: GooglePreviewEmailRequest) =>
    api.post<GooglePreviewEmailResponse>("/api/v1/integrations/google/preview-email", data),
  sendEmail: (data: GoogleSendEmailRequest) =>
    api.post<GoogleSendEmailResponse>("/api/v1/integrations/google/send-email", data),
  listConversations: (filterStatusOrParams?: string | { filterStatus?: string; skip?: number; limit?: number }) => {
    const filterStatus = typeof filterStatusOrParams === "string" ? filterStatusOrParams : filterStatusOrParams?.filterStatus;
    const skip = typeof filterStatusOrParams === "object" ? filterStatusOrParams.skip : undefined;
    const limit = typeof filterStatusOrParams === "object" ? filterStatusOrParams.limit : undefined;

    const query = new URLSearchParams();
    if (filterStatus && filterStatus !== "all") query.set("filter_status", filterStatus);
    if (skip !== undefined) query.set("skip", String(skip));
    if (limit !== undefined) query.set("limit", String(limit));
    const qs = query.toString() ? `?${query.toString()}` : "";
    return api.get<EmailConversationsResponse>(`/api/v1/integrations/google/conversations${qs}`);
  },
  getThread: (candidateId: string) =>
    api.get<EmailThreadResponse>(`/api/v1/integrations/google/threads/${candidateId}`),
  sendReply: (data: { candidate_id: string; message: string; subject?: string }) =>
    api.post<GoogleSendEmailResponse>("/api/v1/integrations/google/reply", data),
  aiDraftReply: (data: { candidate_id: string; instructions?: string | null }) =>
    api.post<{ candidate_id: string; drafted_subject: string; drafted_message: string }>(
      "/api/v1/integrations/google/ai-draft-reply",
      data
    ),
};

// ── Email Conversations & Messaging ────────────────────────────────────────

export interface EmailMessageAttachment {
  filename: string;
  url: string;
  size?: string | null;
  mime_type?: string | null;
}

export interface EmailConversationSummary {
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string | null;
  candidate_stage: string;
  opening_title?: string | null;
  last_message_body?: string | null;
  last_message_subject?: string | null;
  last_message_direction?: string | null;
  last_message_type?: string;
  last_message_at?: string | null;
  unread: boolean;
  unread_count?: number;
  has_attachments?: boolean;
}

export interface EmailConversationsResponse {
  conversations: EmailConversationSummary[];
  total_conversations: number;
  awaiting_reply_count: number;
  unread_count?: number;
}

export interface EmailMessageItem {
  id: string;
  candidate_id: string;
  direction: "inbound" | "outbound" | string;
  message_type?: string;
  subject?: string | null;
  body: string;
  status: string;
  sent_at?: string | null;
  created_at: string;
  thread_id?: string | null;
  attachments?: EmailMessageAttachment[];
}

export interface EmailThreadResponse {
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  candidate_stage: string;
  opening_title?: string | null;
  messages: EmailMessageItem[];
}

// ── Scheduling & Interviews API ──────────────────────────────────────────────

export interface AvailabilityScheduleRead {
  id: string;
  user_id: string;
  timezone: string;
  slot_duration_minutes: number;
  buffer_minutes: number;
  weekly_hours: Record<string, { start: string; end: string }[]>;
  blocked_dates?: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AvailabilityScheduleCreateOrUpdate {
  timezone?: string;
  slot_duration_minutes?: number;
  buffer_minutes?: number;
  weekly_hours: Record<string, { start: string; end: string }[]>;
  blocked_dates?: string[];
  is_active?: boolean;
}

export interface SchedulingLinkRead {
  id: string;
  token: string;
  user_id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  opening_id: string;
  opening_title: string;
  slot_duration_minutes: number;
  status: string;
  expires_at: string;
  public_url: string;
  created_at: string;
}

export interface TimeSlot {
  start_time: string;
  end_time: string;
  start_time_local: string;
  end_time_local: string;
  date_str: string;
  timezone: string;
}

export interface PublicSlotsResponse {
  token: string;
  timezone: string;
  slot_duration_minutes: number;
  slots_by_date: Record<string, TimeSlot[]>;
  total_slots_available: number;
}

export interface InterviewRead {
  id: string;
  user_id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string | null;
  opening_id: string;
  opening_title: string;
  scheduling_link_id?: string | null;
  round_type?: string;
  title: string;
  start_time: string;
  end_time: string;
  timezone: string;
  google_calendar_event_id?: string | null;
  meet_link?: string | null;
  interviewer_email: string;
  status: "scheduled" | "rescheduled" | "cancelled" | "completed" | "passed" | "failed" | "no_show" | string;
  result_status?: "passed" | "failed" | "no_show" | string | null;
  feedback?: string | null;
  result_recorded_at?: string | null;
  cancellation_reason?: string | null;
  cancelled_at?: string | null;
  cancelled_by?: string | null;
  reminder_24h_sent: boolean;
  reminder_1h_sent: boolean;
  created_at: string;
  updated_at: string;
}

export interface PublicSchedulePageInfo {
  token: string;
  status: "active" | "expired" | "booked" | "cancelled" | string;
  expires_at: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string | null;
  opening_title: string;
  round_type?: string;
  slot_duration_minutes: number;
  default_timezone: string;
  interviewer_email: string;
  existing_interview?: InterviewRead | null;
}

export interface InterviewResultRequest {
  result: "passed" | "failed" | "no_show";
  feedback?: string;
}

export interface InterviewResultResponse {
  interview_id: string;
  result_status: "passed" | "failed" | "no_show";
  candidate_id: string;
  candidate_name: string;
  next_action: string;
  next_round?: string | null;
  scheduling_link_token?: string | null;
  scheduling_link_url?: string | null;
  offer_draft_ready: boolean;
}

export interface OfferDraftResponse {
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  opening_id?: string | null;
  opening_title?: string | null;
  status: string;
  subject: string;
  body: string;
  sent_at?: string | null;
}

export interface OfferSendRequest {
  subject: string;
  body: string;
}

export const schedulingApi = {
  getAvailability: () =>
    api.get<AvailabilityScheduleRead>("/api/v1/scheduling/availability"),

  updateAvailability: (data: AvailabilityScheduleCreateOrUpdate) =>
    api.put<AvailabilityScheduleRead>("/api/v1/scheduling/availability", data),

  createLink: (data: { candidate_id: string; round_type?: string; slot_duration_minutes?: number; validity_days?: number }) =>
    api.post<SchedulingLinkRead>("/api/v1/scheduling/links", data),

  getPublicPage: (token: string) =>
    api.get<PublicSchedulePageInfo>(`/api/v1/scheduling/public/${token}`),

  getPublicSlots: (
    token: string,
    params?: { start_date?: string; end_date?: string; tz?: string }
  ) => {
    const q = new URLSearchParams();
    if (params?.start_date) q.set("start_date", params.start_date);
    if (params?.end_date) q.set("end_date", params.end_date);
    if (params?.tz) q.set("tz", params.tz);
    const qs = q.toString();
    return api.get<PublicSlotsResponse>(`/api/v1/scheduling/public/${token}/slots${qs ? `?${qs}` : ""}`);
  },

  bookSlot: (token: string, data: { start_time: string; timezone?: string; notes?: string }) =>
    api.post<InterviewRead>(`/api/v1/scheduling/public/${token}/book`, data),

  candidateReschedule: (
    token: string,
    data: { new_start_time: string; timezone?: string; reason?: string }
  ) => api.post<InterviewRead>(`/api/v1/scheduling/public/${token}/reschedule`, data),

  candidateCancel: (token: string, data: { reason?: string }) =>
    api.post<InterviewRead>(`/api/v1/scheduling/public/${token}/cancel`, data),

  listInterviews: (params?: {
    opening_id?: string;
    candidate_id?: string;
    status?: string;
    from_date?: string;
    to_date?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.opening_id) q.set("opening_id", params.opening_id);
    if (params?.candidate_id) q.set("candidate_id", params.candidate_id);
    if (params?.status) q.set("status", params.status);
    if (params?.from_date) q.set("from_date", params.from_date);
    if (params?.to_date) q.set("to_date", params.to_date);
    const qs = q.toString();
    return api.get<InterviewRead[]>(`/api/v1/scheduling/interviews${qs ? `?${qs}` : ""}`);
  },

  rescheduleInterview: (
    id: string,
    data: { new_start_time: string; timezone?: string; reason?: string }
  ) => api.post<InterviewRead>(`/api/v1/scheduling/interviews/${id}/reschedule`, data),

  cancelInterview: (id: string, data: { reason?: string; cancelled_by?: string }) =>
    api.post<InterviewRead>(`/api/v1/scheduling/interviews/${id}/cancel`, data),

  recordResult: (id: string, data: InterviewResultRequest) =>
    api.post<InterviewResultResponse>(`/api/v1/scheduling/interviews/${id}/result`, data),

  getOfferDraft: (candidateId: string) =>
    api.get<OfferDraftResponse>(`/api/v1/scheduling/offer-draft/${candidateId}`),

  sendOfferLetter: (candidateId: string, data: OfferSendRequest) =>
    api.post<OfferDraftResponse>(`/api/v1/scheduling/offer-draft/${candidateId}/send`, data),

  syncCalendar: () =>
    api.post<CalendarSyncResponse>("/api/v1/scheduling/sync-calendar"),

  getWeekPreview: (startDate?: string) => {
    const q = startDate ? `?start_date=${encodeURIComponent(startDate)}` : "";
    return api.get<AvailabilityWeekPreviewResponse>(`/api/v1/scheduling/availability/week-preview${q}`);
  },

  getBookingLink: () =>
    api.get<SchedulingLinkRead>("/api/v1/scheduling/booking-link"),
};

// ── Google Calendar Live Integration ──────────────────────────────────────────

export interface CalendarAttendee {
  email?: string;
  name?: string;
  response_status?: string;
}

export interface CalendarInterviewData {
  interview_id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string | null;
  opening_id?: string | null;
  opening_title?: string | null;
  round: string;
  status: string;
  result_status?: string | null;
  feedback?: string | null;
  meet_link?: string | null;
}

export interface CalendarEventItem {
  id: string;
  title: string;
  start: string;
  end: string;
  all_day: boolean;
  attendees: CalendarAttendee[];
  meet_link?: string | null;
  status: string;
  color: string;
  is_interview: boolean;
  interview_data?: CalendarInterviewData | null;
}

export interface BusinessHourPeriod {
  days_of_week: number[];
  start_time: string;
  end_time: string;
}

export interface CalendarEventsResponse {
  connected: boolean;
  reconnect_required: boolean;
  message?: string | null;
  time_zone: string;
  business_hours: BusinessHourPeriod[];
  events: CalendarEventItem[];
}

export const calendarApi = {
  getEvents: (params?: { start?: string; end?: string }) => {
    const q = new URLSearchParams();
    if (params?.start) q.set("start", params.start);
    if (params?.end) q.set("end", params.end);
    const qs = q.toString();
    return api.get<CalendarEventsResponse>(`/api/v1/calendar/events${qs ? `?${qs}` : ""}`);
  },
};

export interface CalendarBusyEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  start_local: string;
  end_local: string;
  date_str: string;
}

export interface CalendarBookedInterview {
  id: string;
  candidate_name: string;
  candidate_email: string;
  opening_title: string;
  start_time: string;
  end_time: string;
  start_local: string;
  end_local: string;
  date_str: string;
  meet_link?: string | null;
  status: string;
}

export interface CalendarFreeSlot {
  start_time: string;
  end_time: string;
  start_local: string;
  end_local: string;
  date_str: string;
  is_past: boolean;
}

export interface AvailabilityWeekPreviewResponse {
  week_start: string;
  week_end: string;
  timezone: string;
  slot_duration_minutes: number;
  buffer_minutes: number;
  google_busy_events: CalendarBusyEvent[];
  platform_interviews: CalendarBookedInterview[];
  free_slots: CalendarFreeSlot[];
  booking_link_token: string;
  booking_link_url: string;
}

export interface CalendarSyncResponse {
  synced_count: number;
  updated_count: number;
  cancelled_count: number;
  detail: string;
}

export interface OutreachDraftRequest {
  candidate_id: string;
  channel?: "email";
  language?: "english" | "hinglish";
  instructions?: string;
}

export interface OutreachDraftResponse {
  message_id: string;
  candidate_id: string;
  candidate_name: string;
  channel: string;
  language: string;
  body: string;
  subject?: string;
  scheduling_url?: string;
  status: string;
  ai_drafted: boolean;
  hr_approved: boolean;
  created_at: string;
}

export interface ApprovalQueueItem {
  message_id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string;
  candidate_stage: string;
  opening_id?: string;
  opening_title?: string;
  channel: string;
  language: string;
  body: string;
  subject?: string;
  scheduling_url?: string;
  status: string;
  error_message?: string;
  retry_count: number;
  created_at: string;
}

export interface BulkApproveResponse {
  total: number;
  approved_count: number;
  sent_count: number;
  failed_count: number;
  results: Array<{
    message_id: string;
    candidate_id: string;
    candidate_name: string;
    channel: string;
    status: string;
    error?: string;
  }>;
}

export interface OutreachAuditItem {
  id: string;
  action: string;
  candidate_id?: string;
  candidate_name?: string;
  opening_title?: string;
  from_stage?: string;
  to_stage?: string;
  details?: string;
  failure_reason?: string;
  message_id?: string;
  retryable: boolean;
  created_at: string;
}

export interface StageSyncResponse {
  interviews_checked: number;
  stages_updated_to_interviewed: number;
  candidate_ids_updated: string[];
}

export const outreachApi = {
  draft: (data: OutreachDraftRequest) =>
    api.post<OutreachDraftResponse>("/api/v1/outreach/draft", data),

  getQueue: (params?: { candidate_id?: string; channel?: string }) => {
    const q = new URLSearchParams();
    if (params?.candidate_id) q.set("candidate_id", params.candidate_id);
    if (params?.channel) q.set("channel", params.channel);
    const qs = q.toString();
    return api.get<ApprovalQueueItem[]>(`/api/v1/outreach/queue${qs ? `?${qs}` : ""}`);
  },

  updateDraft: (messageId: string, data: { body: string; subject?: string }) =>
    api.put<ApprovalQueueItem>(`/api/v1/outreach/drafts/${messageId}`, data),

  skip: (messageId: string) =>
    api.delete<{ status: string; message_id: string }>(`/api/v1/outreach/drafts/${messageId}`),

  approve: (messageId: string) =>
    api.post<{ message_id: string; status: string; error?: string }>(`/api/v1/outreach/approve/${messageId}`),

  bulkApprove: (messageIds: string[]) =>
    api.post<BulkApproveResponse>("/api/v1/outreach/bulk-approve", { message_ids: messageIds }),

  retry: (messageId: string) =>
    api.post<{ message_id: string; status: string; error?: string }>(`/api/v1/outreach/retry/${messageId}`),

  getAuditTrail: (params?: { candidate_id?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.candidate_id) q.set("candidate_id", params.candidate_id);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return api.get<OutreachAuditItem[]>(`/api/v1/outreach/audit-trail${qs ? `?${qs}` : ""}`);
  },

  syncStages: () =>
    api.post<StageSyncResponse>("/api/v1/outreach/sync-stages"),
};

// ── Health API ─────────────────────────────────────────────────────────────

export interface DbHealthResponse {
  status: "connected" | "error";
  latency_ms: number;
  host?: string;
  port?: number;
  mode?: "session" | "transaction";
  error?: string;
}

export interface PineconeHealthResponse {
  status: "connected" | "degraded" | "unconfigured" | "error";
  is_connected: boolean;
  index_name: string;
  host?: string | null;
  total_vectors: number;
  dimension: number;
  latency_ms: number;
  embedding_model?: string;
  cloud?: string;
  region?: string;
  cache_hits: number;
  cache_misses: number;
  cache_mode?: string;
  message?: string;
}

export const healthApi = {
  checkDb: () => api.get<DbHealthResponse>("/health/db"),
  checkBackend: () => api.get<{ status: string; database?: string; version: string; environment?: string }>("/health"),
  checkPinecone: () => api.get<PineconeHealthResponse>("/health/pinecone"),
};

// ── Onboarding & Setup Wizard ────────────────────────────────────────────────

export interface HRProfileStep {
  hr_name?: string | null;
  company_name?: string | null;
  hr_role?: string | null;
  email_tone: string;
  signature?: string | null;
  completed: boolean;
}

export interface JobOpeningStep {
  job_opening_id?: string | null;
  job_title?: string | null;
  job_description?: string | null;
  required_skills: string[];
  years_of_experience?: number | null;
  completed: boolean;
}

export interface AvailabilityStep {
  timezone: string;
  slot_duration_minutes: number;
  buffer_minutes: number;
  weekly_hours: Record<string, any>;
  interview_rounds: Array<{ round_name: string; duration_minutes: number }>;
  completed: boolean;
}

export interface TemplatesStep {
  templates: Record<string, { subject: string; body: string }>;
  completed: boolean;
}

export interface OnboardingStatusResponse {
  id: string;
  current_step: number;
  is_completed: boolean;
  agent_started: boolean;
  can_start_agent: boolean;
  completed_steps_count: number;
  total_steps: number;
  progress_percentage: number;
  step_1: HRProfileStep;
  step_2: JobOpeningStep;
  step_3: AvailabilityStep;
  step_4: TemplatesStep;
  created_at: string;
  updated_at: string;
}

export interface GeneratedTemplatesResponse {
  templates: Record<string, { name?: string; subject: string; body: string }>;
  generated_with_ai: boolean;
  model_used?: string | null;
  latency_seconds?: number | null;
}

export interface TemplatePreviewResponse {
  resolved_subject: string;
  resolved_body: string;
}

export const onboardingApi = {
  getStatus: () => api.get<OnboardingStatusResponse>("/api/v1/onboarding"),

  saveStep1: (data: {
    hr_name: string;
    company_name: string;
    hr_role: string;
    email_tone: string;
    signature?: string | null;
  }) => api.post<OnboardingStatusResponse>("/api/v1/onboarding/step/1", data),

  saveStep2: (data: {
    job_title: string;
    job_description: string;
    required_skills: string[];
    years_of_experience?: number | null;
    job_opening_id?: string | null;
  }) => api.post<OnboardingStatusResponse>("/api/v1/onboarding/step/2", data),

  saveStep3: (data: {
    timezone: string;
    slot_duration_minutes: number;
    buffer_minutes: number;
    weekly_hours: Record<string, any>;
    interview_rounds: Array<{ round_name: string; duration_minutes: number }>;
  }) => api.post<OnboardingStatusResponse>("/api/v1/onboarding/step/3", data),

  saveStep4: (data: {
    templates: Record<string, { subject: string; body: string; name?: string }>;
  }) => api.post<OnboardingStatusResponse>("/api/v1/onboarding/step/4", data),

  generateTemplates: (data: {
    hr_name?: string;
    company_name?: string;
    hr_role?: string;
    email_tone?: string;
    single_template_key?: string;
  }) => api.post<GeneratedTemplatesResponse>("/api/v1/onboarding/generate-templates", data),

  previewTemplate: (data: {
    subject: string;
    body: string;
    candidate_name?: string;
    role?: string;
    company?: string;
    hr_name?: string;
    interview_date?: string;
    interview_time?: string;
    meet_link?: string;
    schedule_link?: string;
    job_details?: string;
  }) => api.post<TemplatePreviewResponse>("/api/v1/onboarding/preview-template", data),

  startAgent: () =>
    api.post<{ status: string; agent_started: boolean; message: string }>("/api/v1/onboarding/start-agent"),
};

// ── CV Review Flow API ───────────────────────────────────────────────────────

export interface CVReviewQueueItem {
  id: string;
  user_id: string;
  opening_id: string;
  opening_title: string;
  opening_pass_mark: number;
  pass_mark?: number;
  name: string;
  email: string;
  cv_text?: string;
  cv_file_url?: string | null;
  score?: number | null;
  recommendation: "Recommended" | "Borderline" | "Not recommended" | "Unscored";
  matched_skills: string[];
  missing_skills: string[];
  red_flags: string[];
  summary?: string | null;
  stage: string;
  review_status: "pending" | "approved" | "rejected";
  review_decision_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CVReviewDecisionPayload {
  candidate_ids: string[];
  action: "approve" | "reject";
  notes?: string;
}

export interface CVReviewDecisionResponse {
  total_processed: number;
  approved_count: number;
  rejected_count: number;
  results: Array<{
    candidate_id: string;
    candidate_name: string;
    action: string;
    status: string;
    stage: string;
    emails_sent: string[];
    scheduling_link?: string | null;
    error?: string | null;
  }>;
}

export const cvReviewApi = {
  getQueue: (params?: { opening_id?: string; status?: string; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.opening_id && params.opening_id !== "all") searchParams.set("opening_id", params.opening_id);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.search) searchParams.set("search", params.search);
    const qs = searchParams.toString();
    return api.get<CVReviewQueueItem[]>(`/api/v1/cv-review/queue${qs ? `?${qs}` : ""}`);
  },

  decide: (data: CVReviewDecisionPayload) =>
    api.post<CVReviewDecisionResponse>("/api/v1/cv-review/decision", data),

  scoreCandidate: (candidateId: string, forceRerun: boolean = false) =>
    api.post<CVReviewQueueItem>(`/api/v1/cv-review/score/${candidateId}?force_rerun=${forceRerun}`),

  updatePassMark: (openingId: string, passMark: number) =>
    api.patch<JobOpening>(`/api/v1/cv-review/opening/${openingId}/pass-mark`, { pass_mark: passMark }),
};

// ── Agent Settings & Activity Dashboard API ───────────────────────────────────

export interface AgentSettingsRead {
  id: string;
  user_id: string;
  is_paused: boolean;
  paused_at?: string | null;
  paused_reason?: string | null;
  daily_send_limit: number;
  sends_today: number;
  sends_remaining: number;
  notify_email?: string | null;
  notify_on_booking: boolean;
  notify_on_reply: boolean;
  notify_on_failure: boolean;
  daily_summary_enabled: boolean;
  daily_summary_time: string;
  last_daily_summary_sent_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentSettingsUpdate {
  is_paused?: boolean;
  paused_reason?: string;
  daily_send_limit?: number;
  notify_email?: string;
  notify_on_booking?: boolean;
  notify_on_reply?: boolean;
  notify_on_failure?: boolean;
  daily_summary_enabled?: boolean;
  daily_summary_time?: string;
}

export interface AgentPauseToggleRequest {
  paused?: boolean;
  reason?: string;
}

export interface AgentActivityFeedItem {
  id: string;
  timestamp: string;
  action: string;
  category: "cv_review" | "interview" | "outreach" | "system" | "error";
  title: string;
  details: string;
  candidate_id?: string | null;
  candidate_name?: string | null;
}

export interface AgentTodayActivityResponse {
  is_paused: boolean;
  paused_reason?: string | null;
  daily_send_limit: number;
  sends_today: number;
  sends_remaining: number;
  cvs_ingested_today: number;
  cvs_scored_today: number;
  waiting_for_review: number;
  interviews_today: number;
  failures_today: number;
  feed: AgentActivityFeedItem[];
}

export interface DailySummarySendRequest {
  recipient_email?: string;
  force?: boolean;
}

export interface DailySummarySendResponse {
  status: string;
  recipient: string;
  sent_at: string;
  summary: {
    cvs_received_today: number;
    candidates_waiting_review: number;
    interviews_scheduled_today: number;
    outbound_messages_sent: number;
    failures_today: number;
  };
  preview: string;
}

export const agentApi = {
  getSettings: () => api.get<AgentSettingsRead>("/api/v1/agent/settings"),
  updateSettings: (data: AgentSettingsUpdate) =>
    api.put<AgentSettingsRead>("/api/v1/agent/settings", data),
  togglePause: (data?: AgentPauseToggleRequest) =>
    api.post<AgentSettingsRead>("/api/v1/agent/pause", data || {}),
  getTodayActivity: () =>
    api.get<AgentTodayActivityResponse>("/api/v1/agent/today-activity"),
  sendDailySummary: (data?: DailySummarySendRequest) =>
    api.post<DailySummarySendResponse>("/api/v1/agent/send-daily-summary", data || {}),
  testFailureAlert: () =>
    api.post<{ status: string; message: string }>("/api/v1/agent/test-failure-alert", {}),
};

export interface PipelineAgentStatusResponse {
  status: string;
  background_worker: string;
  active_candidates: number;
  timestamp: string;
}

export interface PipelineAgentLog {
  candidate_id: string;
  previous_status: string;
  new_status: string;
  action_taken: string;
  template_sent?: string | null;
  next_pending_action?: string | null;
  timer_set?: string | null;
  timestamp: string;
}

export const pipelineAgentApi = {
  getStatus: () =>
    api.get<PipelineAgentStatusResponse>("/api/v1/pipeline-agent/status"),
  runCycle: () =>
    api.post<{ result: any; timestamp: string }>("/api/v1/pipeline-agent/cycle"),
  hrReview: (payload: { candidate_id: string; decision: "approve" | "reject" | "on_hold"; feedback?: string }) =>
    api.post("/api/v1/pipeline-agent/hr-review", payload),
  candidateReply: (payload: { candidate_id: string; reply_body: string }) =>
    api.post("/api/v1/pipeline-agent/candidate-reply", payload),
  interviewDecision: (payload: { candidate_id: string; round_name?: string; decision: "pass" | "reject"; feedback?: string }) =>
    api.post("/api/v1/pipeline-agent/interview-decision", payload),
  offerAction: (payload: { candidate_id: string; action_type: string; details?: Record<string, any> }) =>
    api.post("/api/v1/pipeline-agent/offer-action", payload),
  getCandidateHistory: (candidateId: string) =>
    api.get<{ candidate_id: string; current_status: string; pipeline_logs: PipelineAgentLog[] }>(
      `/api/v1/pipeline-agent/candidate/${candidateId}/history`
    ),
};

export interface RecruitingTemplateModel {
  id: string;
  user_id: string;
  stage_key: string;
  name: string;
  description?: string | null;
  subject: string;
  body: string;
  is_active: boolean;
  is_default: boolean;
  is_custom: boolean;
  created_at: string;
  updated_at: string;
}

export const recruitingTemplatesApi = {
  list: () => api.get<RecruitingTemplateModel[]>("/api/v1/recruiting-templates"),
  create: (data: {
    stage_key: string;
    name: string;
    description?: string;
    subject: string;
    body: string;
    is_active?: boolean;
    is_default?: boolean;
    is_custom?: boolean;
  }) => api.post<RecruitingTemplateModel>("/api/v1/recruiting-templates", data),
  update: (id: string, data: Partial<RecruitingTemplateModel>) =>
    api.put<RecruitingTemplateModel>(`/api/v1/recruiting-templates/${id}`, data),
  duplicate: (id: string) =>
    api.post<RecruitingTemplateModel>(`/api/v1/recruiting-templates/${id}/duplicate`),
  toggle: (id: string) =>
    api.post<RecruitingTemplateModel>(`/api/v1/recruiting-templates/${id}/toggle`),
  setDefault: (id: string) =>
    api.post<RecruitingTemplateModel>(`/api/v1/recruiting-templates/${id}/set-default`),
  delete: (id: string) =>
    api.delete(`/api/v1/recruiting-templates/${id}`),
  batchSave: (templates: Record<string, { id?: string; subject: string; body: string; name?: string; is_active?: boolean }>) =>
    api.post<{ message: string; count: number }>("/api/v1/recruiting-templates/batch", { templates }),
  regenerate: (data?: { single_template_key?: string }) =>
    api.post<{
      templates: Record<string, { name: string; subject: string; body: string }>;
      success: boolean;
      model_used: string;
      latency_seconds: number;
    }>("/api/v1/recruiting-templates/regenerate", data || {}),
};



