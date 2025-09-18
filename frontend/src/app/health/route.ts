// app/health/route.ts
export async function GET() {
  // lightweight JSON response for container healthchecks
  return new Response(
    JSON.stringify({ ok: true, ts: new Date().toISOString() }),
    {
      status: 200,
      headers: { "Content-Type": "application/json" },
    },
  );
}
