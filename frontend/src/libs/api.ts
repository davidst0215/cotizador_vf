// src/libs/api.ts
// En servidor (SSR): usa INTERNAL_API_URL para comunicarse internamente con el backend
// En cliente (browser): siempre usa el proxy para evitar problemas de CORS
const BASE =
  typeof window === "undefined"
    ? process.env.INTERNAL_API_URL || "http://localhost:8001"
    : `${process.env.NEXT_PUBLIC_BASE_PATH || ""}/api/proxy`.replace(/\/{2,}/g, "/");

function joinPath(path: string) {
  return `${BASE}/${path.replace(/^\//, "")}`;
}

async function createHttpError(res: Response) {
  let message = `HTTP ${res.status} ${res.statusText}`;
  try {
    const payload = await res.json();
    message = payload?.mensaje || payload?.message || JSON.stringify(payload);
  } catch {
    // ignore parse errors
  }
  const err = new Error(message) as Error & { status?: number; response?: Response };
  err.status = res.status;
  err.response = res;
  return err;
}

export async function get<T = unknown>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = joinPath(path);
  const res = await fetch(url, { credentials: "include", ...init });
  if (!res.ok) throw await createHttpError(res);
  return (await res.json()) as T;
}

export async function post<T = unknown>(
  path: string,
  body?: unknown,
  init?: RequestInit,
): Promise<T> {
  const url = joinPath(path);
  const headers = new Headers(init?.headers || {});
  if (!headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");

  const res = await fetch(url, {
    method: "POST",
    credentials: "include",
    body: body === undefined ? undefined : JSON.stringify(body),
    ...init,
    headers,
  });

  if (!res.ok) throw await createHttpError(res);
  return (await res.json()) as T;
}
