import axios, { AxiosError } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const api = axios.create({
  baseURL,
  timeout: 20000,
  headers: { Accept: "application/json" },
});

export interface ApiError {
  status: number;
  message: string;
  detail?: unknown;
}

function normalizeError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const status = error.response?.status ?? 0;
    const data = error.response?.data as { detail?: unknown } | undefined;
    const detail = data?.detail;
    let message: string;
    if (typeof detail === "string") message = detail;
    else if (status === 404) message = "Not found";
    else if (status === 0) message = "Cannot reach the API server";
    else if (status >= 500) message = "The server encountered an error";
    else message = error.message || "Request failed";
    return { status, message, detail };
  }
  return { status: 0, message: "Unexpected error" };
}

// Attach a lightweight request id for tracing.
api.interceptors.request.use((config) => {
  config.headers.set(
    "X-Request-Id",
    Math.random().toString(36).slice(2, 10),
  );
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => Promise.reject(normalizeError(error)),
);

/** Set the reviewer identity sent with review decisions. */
export function setReviewerId(reviewerId: string) {
  api.defaults.headers.common["X-Reviewer-Id"] = reviewerId;
}
