const BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/$/, "");

function joinPath(path: string) {
  return `${BASE}/${path.replace(/^\//, "")}`;
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
