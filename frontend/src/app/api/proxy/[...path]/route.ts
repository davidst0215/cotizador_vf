// app/api/proxy/[...path]/route.ts
import type { NextRequest } from "next/server";

// server-only internal API (e.g. "http://internal-api:8000")
// Default to localhost:8000 since frontend and backend always run on same machine
const INTERNAL_API_URL = process.env.INTERNAL_API_URL || "http://localhost:8000";
const PROXY_TIMEOUT_MS = parseInt(process.env.PROXY_TIMEOUT_MS || "10000", 10);
const PROXY_ALLOWLIST = (process.env.PROXY_ALLOWLIST || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean); // optional: allowed path prefixes

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "set-cookie", // don't forward cookies from internal API by default
]);

function invalidPath(path: string) {
  if (!path) return true;
  if (path.includes("..")) return true;
  if (/^https?:\/\//i.test(path)) return true;

  // allow URL-encoded characters
  if (!/^[\w\-\/%]+$/.test(path)) return true;

  if (PROXY_ALLOWLIST.length) {
    return !PROXY_ALLOWLIST.some((p) => path.startsWith(p));
  }
  return false;
}

async function forward(req: NextRequest, method: string) {
  const segs = (req.nextUrl.pathname || "").split("/").filter(Boolean);
  // last segments are 'api','proxy',... ; we want the parts after /api/proxy/
  const proxyIndex = segs.findIndex((s) => s === "proxy");
  const pathSegments = proxyIndex >= 0 ? segs.slice(proxyIndex + 1) : segs;
  const path = pathSegments.join("/");

  if (invalidPath(path)) {
    return new Response("invalid or disallowed path", { status: 400 });
  }

  const query = req.nextUrl.search || "";
  // empty => we will proxy to internal-relative path (not recommended)
  const targetBase = INTERNAL_API_URL || "";
  const target = `${targetBase.replace(/\/$/, "")}/${path}${query}`;

  // forward headers: only the useful ones
  const headers = new Headers();
  const incoming = req.headers;
  const cookie = incoming.get("cookie");
  if (cookie) headers.set("cookie", cookie);
  const auth = incoming.get("authorization");
  if (auth) headers.set("authorization", auth);

  // content-type for write methods
  const contentType = incoming.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  // Body handling
  let body: BodyInit | undefined;
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    try {
      body = await req.arrayBuffer();
    } catch {
      // fallthrough with undefined body
    }
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), PROXY_TIMEOUT_MS);

  try {
    const res = await fetch(target, {
      method,
      headers,
      body: (body as ArrayBuffer | Uint8Array)?.byteLength ? body : undefined,
      signal: controller.signal,
    });

    // copy response body
    const arrayBuffer = await res.arrayBuffer();
    const outHeaders = new Headers();
    res.headers.forEach((v, k) => {
      if (!HOP_BY_HOP.has(k.toLowerCase())) outHeaders.set(k, v);
    });

    return new Response(arrayBuffer, {
      status: res.status,
      headers: outHeaders,
    });
  } catch (err: any) {
    if (err.name === "AbortError") {
      return new Response("upstream timeout", { status: 504 });
    }
    return new Response(`upstream error: ${String(err?.message || err)}`, {
      status: 502,
    });
  } finally {
    clearTimeout(timeout);
  }
}

// Export handlers for the HTTP methods we want to support
export async function GET(req: NextRequest) {
  return forward(req, "GET");
}
export async function POST(req: NextRequest) {
  return forward(req, "POST");
}
export async function PUT(req: NextRequest) {
  return forward(req, "PUT");
}
export async function PATCH(req: NextRequest) {
  return forward(req, "PATCH");
}
export async function DELETE(req: NextRequest) {
  return forward(req, "DELETE");
}
