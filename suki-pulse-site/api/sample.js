import { guard, json } from './_lib.js';
import ITEMS from './_items.js';

// Random real (fictional sandbox) complaints. Free: no model calls, so no passcode needed.
export function GET(request) {
  const denied = guard(request, { route: 'sample', max: 60, windowMs: 60_000, needCode: false });
  if (denied) return denied;
  const n = Math.max(1, Math.min(5, Number(new URL(request.url).searchParams.get('n')) || 1));
  const pick = [...ITEMS].sort(() => Math.random() - 0.5).slice(0, n);
  return json(200, pick);
}
