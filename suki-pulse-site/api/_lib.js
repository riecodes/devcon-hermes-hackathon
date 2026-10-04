// Shared helpers for the Jev Live Race functions. Keys come ONLY from env vars and never leave the server.
import { timingSafeEqual } from 'node:crypto';

export const CAUSES = {
  late_delivery: 'The delivery was late, never arrived, or the rider behaved badly.',
  spoiled_damaged: 'An item arrived spoiled, expired, damaged, or not fresh.',
  out_of_stock: 'An item was missing, out of stock, substituted, or the wrong item was sent.',
  loyalty: 'Loyalty / Suki card points are missing, wrong, or expired unfairly.',
  promo: 'A promo or discount code did not work or was not applied.',
  payment_refund: 'A payment failed, the customer was double-charged, or wants a refund.'
};
const EXTRA = {
  mentions_rider: 'Does the customer mention the rider or delivery person?',
  wants_callback: 'Does the customer ask to be contacted or called back?',
  mentions_price: 'Does the customer complain about prices or being overcharged?',
  mentions_app: 'Does the customer mention the app or website?',
  mentions_staff: 'Does the customer mention store staff?',
  mentions_cleanliness: 'Does the customer mention cleanliness?',
  positive_tone: 'Is the overall tone of the message positive?',
  repeat_issue: 'Does the customer say this happened before?'
};
const PRICE = { jev_in: 0.042, llm_in: 1.0, llm_out: 5.0 }; // USD per 1M tokens
export const LIMITS = { textChars: 600, maxQuestions: 16, batchMax: 20, concurrency: 8, timeoutMs: 20000 };

const LLM_SYSTEM =
  'You classify Suki Mart (Philippine grocery chain) customer complaints. Reply with ONLY a JSON object, no prose: ' +
  '{"late_delivery": p, "spoiled_damaged": p, "out_of_stock": p, "loyalty": p, "promo": p, "payment_refund": p, ' +
  '"churn_risk": 0|1|2, "urgent": p} where each p is the probability (0 to 1) that the complaint is about that cause. ' +
  'Causes: ' + Object.entries(CAUSES).map(([k, v]) => `${k}: ${v}`).join(' ') +
  ' churn_risk: 0 low, 1 medium, 2 high. urgent: needs a same-day response (money lost, food safety, angry customer).';

const state = (text) => `Suki Mart (Philippine grocery) message #0. Customer wrote: ${text}`;

function questions(q) {
  const qs = {};
  for (const [k, v] of Object.entries(CAUSES)) qs[k] = { type: 'noul', instructions: `Does the customer complain about this? ${v}` };
  qs.churn_risk = { type: 'score', instructions: 'How likely is this customer to stop shopping at Suki Mart?',
    criteria: ['Low: mild, likely to stay', 'Medium: annoyed, could leave', 'High: angry, threatening to leave or already gone'] };
  qs.urgent = { type: 'noul', instructions: 'Does this need a same-day response (money lost, food safety, angry customer)?' };
  Object.entries(EXTRA).slice(0, Math.max(0, q - 8)).forEach(([k, v]) => { qs[k] = { type: 'noul', instructions: v }; });
  return q < 8 ? Object.fromEntries(Object.entries(qs).slice(0, q)) : qs;
}

async function post(url, headers, body) {
  const t0 = performance.now();
  const r = await fetch(url, {
    method: 'POST', body: JSON.stringify(body), signal: AbortSignal.timeout(LIMITS.timeoutMs),
    headers: { 'Content-Type': 'application/json', 'User-Agent': 'suki-pulse/1.0', ...headers }
  });
  if (!r.ok) throw new Error(`upstream ${r.status}`);
  const data = await r.json();
  return { data, ms: Math.round((performance.now() - t0) * 10) / 10 };
}

export async function jev(text, q = 8) {
  const key = (process.env.TYPESAFE_API_KEY || '').trim();
  if (!key) throw new Error('server missing Jev key');
  const { data, ms } = await post('https://api.typesafe.ai/v1/systemone', { Authorization: `Bearer ${key}` },
    { model: 'jev-1.13.0', state: state(text), questions: questions(q) });
  const a = data.answers || {};
  const causes = {};
  for (const c of Object.keys(CAUSES)) if (a[c]) causes[c] = Math.round(Number(a[c].noul) * 1000) / 1000;
  const tin = Number(data.usage?.input_tokens || 0);
  const top = Object.keys(causes).sort((x, y) => causes[y] - causes[x])[0] || null;
  return { ms, tokens_in: tin, tokens_out: 0, cost_usd: (tin * PRICE.jev_in) / 1e6, causes,
    churn_risk: a.churn_risk ? Number(a.churn_risk.score) : null, urgent: a.urgent ? Number(a.urgent.noul) : null, top };
}

export async function llm(text) {
  const key = (process.env.OPENCODE_ZEN_API_KEY || '').trim();
  if (!key) throw new Error('server missing Zen key');
  const { data, ms } = await post('https://opencode.ai/zen/v1/messages', { 'x-api-key': key, 'anthropic-version': '2023-06-01' },
    { model: 'claude-haiku-4-5', max_tokens: 200, system: LLM_SYSTEM, messages: [{ role: 'user', content: state(text) }] });
  const raw = (data.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('');
  let parsed = {};
  const m = raw.match(/\{[\s\S]*\}/);
  if (m) { try { parsed = JSON.parse(m[0]); } catch { parsed = {}; } }
  const causes = {};
  for (const c of Object.keys(CAUSES)) causes[c] = Math.round(Number(parsed[c] || 0) * 1000) / 1000;
  const tin = Number(data.usage?.input_tokens || 0), tout = Number(data.usage?.output_tokens || 0);
  const top = Object.values(causes).some((v) => v > 0) ? Object.keys(causes).sort((x, y) => causes[y] - causes[x])[0] : null;
  return { ms, tokens_in: tin, tokens_out: tout, cost_usd: (tin * PRICE.llm_in + tout * PRICE.llm_out) / 1e6, causes,
    churn_risk: Number(parsed.churn_risk || 0), urgent: Number(parsed.urgent || 0), top };
}

// ---------- guardrails ----------
const json = (status, obj) => new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });

function codeOk(code) {
  const want = (process.env.DEMO_PASSCODE || '').trim();
  if (!want || !code) return false;
  const a = Buffer.from(String(code)), b = Buffer.from(want);
  return a.length === b.length && timingSafeEqual(a, b);
}

// Best-effort per-instance limiter (a function instance is reused while warm). The prepaid
// API balances are the hard ceiling; this keeps one visitor from draining them quickly.
const hits = new Map();
function limited(key, max, windowMs) {
  const now = Date.now();
  const arr = (hits.get(key) || []).filter((t) => now - t < windowMs);
  if (arr.length >= max) { hits.set(key, arr); return true; }
  arr.push(now); hits.set(key, arr);
  if (hits.size > 5000) hits.clear();
  return false;
}

/** Shared checks. Returns a Response to send back on rejection, or null to continue. */
export function guard(request, { route, max, windowMs, needCode = true }) {
  const url = new URL(request.url);
  const origin = request.headers.get('origin');
  if (origin && new URL(origin).host !== url.host) return json(403, { error: 'Cross-site requests are not allowed.' });
  const ip = (request.headers.get('x-forwarded-for') || 'unknown').split(',')[0].trim();
  // Count the attempt BEFORE checking the code, so wrong guesses are rate-limited too.
  if (limited(`${route}:${ip}`, max, windowMs)) return json(429, { error: 'Too many tries. Wait a minute and try again.' });
  if (needCode && !codeOk(url.searchParams.get('code'))) return json(401, { error: 'Wrong or missing demo passcode.' });
  return null;
}

export function cleanText(url) {
  return (url.searchParams.get('text') || '').trim().slice(0, LIMITS.textChars);
}

export function sse(run) {
  const enc = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const send = (event, data) => controller.enqueue(enc.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));
      try { await run(send); } catch (e) { send('result', { model: 'jev', error: 'Server error' }); }
      controller.close();
    }
  });
  return new Response(stream, { headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache, no-transform', 'X-Accel-Buffering': 'no' } });
}

export { json };
