import { cleanText, guard, jev, json, LIMITS, llm, sse } from './_lib.js';

// One complaint, both models at once. Each result is streamed the moment it lands.
export function GET(request) {
  const denied = guard(request, { route: 'race', max: 6, windowMs: 60_000 });
  if (denied) return denied;
  const url = new URL(request.url);
  const text = cleanText(url);
  if (!text) return json(400, { error: 'Type or pick a complaint first.' });
  const q = Math.max(1, Math.min(LIMITS.maxQuestions, Number(url.searchParams.get('questions')) || 8));
  return sse(async (send) => {
    const t0 = performance.now();
    send('start', { t0: 0 });
    const run = (model, fn) => fn().then(
      (r) => send('result', { model, elapsed_ms: Math.round(performance.now() - t0), ...r }),
      () => send('result', { model, error: 'The model call failed. Try again.' }));
    await Promise.all([run('jev', () => jev(text, q)), run('llm', () => llm(text))]);
    send('done', {});
  });
}
