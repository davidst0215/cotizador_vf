// src/libs/api.ts
const rawPublic = process.env.NEXT_PUBLIC_API_URL; // optional
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? ""; // bake if basePath
const rawServer = process.env.INTERNAL_API_URL; // runtime-only server upstream

const BASE = rawPublic
  ? String(rawPublic).replace(/\/$/, "")
  : (typeof window === "undefined" && String(rawServer).startsWith("http")
      ? String(rawServer).replace(/\/$/, "")
      : `${basePath}/api/proxy`.replace(/\/$/, ""));

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
  const err: any = new Error(message);
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
