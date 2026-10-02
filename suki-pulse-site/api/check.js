import { guard, json } from './_lib.js';

// Passcode check for the page's gate. Rate-limited so the code can't be brute-forced quickly.
export function GET(request) {
  return guard(request, { route: 'check', max: 10, windowMs: 60_000 }) || json(200, { ok: true });
}
