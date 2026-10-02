import { guard, jev, json, LIMITS, llm, sse } from './_lib.js';
import ITEMS from './_items.js';

// Up to 20 complaints, 8 calls open per model, both models racing at once. The costliest
// route, so it gets the tightest limit: 2 batches per visitor per 5 minutes.
export function GET(request) {
  const denied = guard(request, { route: 'batch', max: 2, windowMs: 300_000 });
  if (denied) return denied;
  const url = new URL(request.url);
  const n = Math.max(5, Math.min(LIMITS.batchMax, Number(url.searchParams.get('n')) || 20));
  const c = Math.max(1, Math.min(LIMITS.concurrency, Number(url.searchParams.get('concurrency')) || 8));
  const picks = [...ITEMS].sort(() => Math.random() - 0.5).slice(0, n);
  return sse(async (send) => {
    const t0 = performance.now();
    send('start', { n, concurrency: c });
    const lane = async (model, fn) => {
      let next = 0, ok = 0, cost = 0;
      const worker = async () => {
        while (next < picks.length) {
          const i = next++;
          try {
            const r = await fn(picks[i].text);
            ok++; cost += r.cost_usd;
            send('tick', { model, i, ms: r.ms, top: r.top, ok: true, elapsed_ms: Math.round(performance.now() - t0) });
          } catch {
            send('tick', { model, i, ok: false, top: null, elapsed_ms: Math.round(performance.now() - t0) });
          }
        }
      };
      await Promise.all(Array.from({ length: c }, worker));
      const wall = performance.now() - t0;
      send('summary', { model, wall_ms: Math.round(wall), per_sec: Math.round((n / (wall / 1000)) * 100) / 100, cost_usd: cost, ok });
    };
    await Promise.all([lane('jev', (t) => jev(t)), lane('llm', (t) => llm(t))]);
    send('done', {});
  });
}
