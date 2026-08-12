import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  clearTokens,
  getTokens,
  redirectToLogin,
  setTokens,
} from "@/lib/auth-storage";
import type { TokenResponse } from "@/lib/types";

const API_URL =
  process.env.NEXT_PUBLIC_PYTHON_API_URL ?? "http://127.0.0.1:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 20000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const tokens = getTokens();
  if (tokens?.access_token) {
    config.headers = AxiosHeaders.from(config.headers);
    config.headers.set("Authorization", `Bearer ${tokens.access_token}`);
  }
  return config;
});

let isRefreshing = false;
let refreshQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}> = [];

async function refreshAccessToken(): Promise<string | null> {
  const tokens = getTokens();
  if (!tokens?.refresh_token) return null;
  try {
    const { data } = await axios.post<TokenResponse>(
      `${API_URL}/auth/refresh`,
      { refresh_token: tokens.refresh_token },
      { headers: { "Content-Type": "application/json" } }
    );
    setTokens({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    });
    return data.access_token;
  } catch {
    return null;
  }
}

function flushQueue(accessToken: string | null, error?: unknown) {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (accessToken) resolve(accessToken);
    else reject(error ?? new Error("Session expired"));
  });
  refreshQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    if (!original || error.response?.status !== 401 || original._retry) {
      throw error;
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject });
      }).then((token) => {
        original.headers = AxiosHeaders.from(original.headers);
        original.headers.set("Authorization", `Bearer ${token as string}`);
        return api(original);
      });
    }

    original._retry = true;
    isRefreshing = true;

    const newToken = await refreshAccessToken();
    flushQueue(newToken, error);

    if (!newToken) {
      clearTokens();
      redirectToLogin();
      throw error;
    }

    original.headers = AxiosHeaders.from(original.headers);
    original.headers.set("Authorization", `Bearer ${newToken}`);
    return api(original);
  }
);

export interface ApiErrorPayload {
  detail?: string | Array<{ loc: string[]; msg: string }> | null;
}

export class ApiError extends Error {
  status: number | null;
  details: ApiErrorPayload["detail"] | null;

  constructor(status: number | null, message: string, details: ApiErrorPayload["detail"] = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const payload = (error.response?.data ?? {}) as ApiErrorPayload;
    const status = error.response?.status ?? null;
    const message = messageFromDetail(payload.detail, status);
    return new ApiError(status, message, payload.detail ?? null);
  }
  return new ApiError(null, "Something went wrong. Please try again.");
}

function messageFromDetail(
  detail: ApiErrorPayload["detail"],
  status: number | null
): string {
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(" ");
  }
  if (status === 401) return "Your session has expired. Please log in again.";
  if (status === 403) return "You do not have permission to perform this action.";
  if (status === 404) return "Resource not found.";
  if (status === 409) {
    return "Unable to complete this action because the resource already exists or conflicts with existing data.";
  }
  return "Something went wrong. Please try again.";
}

export function formatError(error: unknown): string {
  return toApiError(error).message;
}

export function getErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  const message = formatError(error);
  return message || fallback;
}

export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await api.get<T>(url, config);
  return data;
}

export async function post<T>(url: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await api.post<T>(url, body, config);
  return data;
}

export async function patch<T>(url: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await api.patch<T>(url, body, config);
  return data;
}

export async function remove(url: string, config?: AxiosRequestConfig): Promise<void> {
  await api.delete(url, config);
}
