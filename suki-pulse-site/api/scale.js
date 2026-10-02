import { cleanText, guard, jev, json, LIMITS } from './_lib.js';

// Jev only, 1 to 16 questions per call: shows latency stays flat as questions grow.
export async function GET(request) {
  const denied = guard(request, { route: 'scale', max: 12, windowMs: 60_000 });
  if (denied) return denied;
  const url = new URL(request.url);
  const text = cleanText(url);
  if (!text) return json(400, { error: 'Type or pick a complaint first.' });
  const k = Math.max(1, Math.min(LIMITS.maxQuestions, Number(url.searchParams.get('questions')) || 8));
  try {
    const r = await jev(text, k);
    return json(200, { questions: k, ms: r.ms, tokens_in: r.tokens_in, cost_usd: r.cost_usd });
  } catch {
    return json(502, { error: 'The Jev call failed. Try again.' });
  }
}
