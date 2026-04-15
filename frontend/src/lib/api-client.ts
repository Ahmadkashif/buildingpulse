import type { ApiError } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  params?: Record<string, string>;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, params, ...init } = options;

  const url = new URL(path, API_BASE_URL || "http://localhost:3000");
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }

  const response = await fetch(url.toString(), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      message: response.statusText,
      code: "UNKNOWN",
      status: response.status,
    }));
    throw error;
  }

  if (response.status === 204) return undefined as T;

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, opts?: RequestOptions) => request<T>(path, { ...opts, method: "GET" }),
  post: <T>(path: string, opts?: RequestOptions) => request<T>(path, { ...opts, method: "POST" }),
  put: <T>(path: string, opts?: RequestOptions) => request<T>(path, { ...opts, method: "PUT" }),
  patch: <T>(path: string, opts?: RequestOptions) => request<T>(path, { ...opts, method: "PATCH" }),
  delete: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "DELETE" }),
};
