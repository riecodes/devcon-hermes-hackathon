"""Build the Vercel copy of the live race: ../jev-live-race/{index.html, api/_items.js}.

The local app (app.py on 127.0.0.1:8790) is untouched. This copy adds a demo-passcode gate,
sends the passcode on every API call, and drops the 40-complaint batch (server caps at 20).
No keys are written anywhere: the deployed functions read them from Vercel env vars.
"""
import json
import os

from bench import load_items

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "suki-pulse-site")  # one site: / dashboard, /race, /benchmark
os.makedirs(os.path.join(OUT, "api"), exist_ok=True)
os.makedirs(os.path.join(OUT, "race"), exist_ok=True)

page = open(os.path.join(HERE, "live.html"), encoding="utf-8").read()
edits = [
    ('          <button type="button" data-n="40" aria-pressed="false">40</button>\n', ""),
    ("fetch('/api/sample?n=1')", "fetch(withCode('/api/sample?n=1'))"),
    ("const url = `/api/race?text=${encodeURIComponent(text)}&questions=8`;",
     "const url = withCode(`/api/race?text=${encodeURIComponent(text)}&questions=8`);"),
    ("const url = `/api/batch?n=${batchN}&concurrency=8`;", "const url = withCode(`/api/batch?n=${batchN}&concurrency=8`);"),
    ("fetch(`/api/scale?text=${encodeURIComponent(text)}&questions=${q}`)",
     "fetch(withCode(`/api/scale?text=${encodeURIComponent(text)}&questions=${q}`))"),
    ('href="/recorded"', 'href="/benchmark/"'),
]
for old, new in edits:
    assert old in page, f"anchor not found: {old[:60]}"
    page = page.replace(old, new)

gate = """
<style>
#gate { position: fixed; inset: 0; z-index: 50; display: grid; place-items: center; background: var(--bg); padding: 16px; }
#gate form { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 22px; display: grid; gap: 12px; width: min(420px, 100%); }
#gate h2 { margin: 0; font-family: var(--f-display); text-transform: uppercase; }
#gate p { margin: 0; color: var(--ink-2); font-size: 0.92rem; }
#gate input { font: 500 1rem var(--f-mono); padding: 9px 11px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--ink); }
#gate button { font: 600 0.95rem var(--f-body); padding: 9px 14px; border-radius: 8px; border: 0; background: var(--jev); color: #fff; cursor: pointer; }
#gate .err { color: var(--llm); min-height: 1.2em; font-size: 0.88rem; }
</style>
<div id="gate">
  <form id="gate-form">
    <h2>Jev Live Race</h2>
    <p>Live calls spend real API credits, so this demo needs the passcode from the Camp Run team.</p>
    <label for="gate-code" class="eyebrow">Demo passcode</label>
    <input id="gate-code" autocomplete="off" spellcheck="false" required>
    <button type="submit">Enter</button>
    <div class="err" id="gate-err" aria-live="polite"></div>
    <p><a href="/benchmark/">See the recorded benchmark instead</a></p>
  </form>
</div>
<script>
let DEMO_CODE = '';
try { DEMO_CODE = sessionStorage.getItem('jevDemoCode') || ''; } catch (e) {}
function withCode(u) { return u + (u.includes('?') ? '&' : '?') + 'code=' + encodeURIComponent(DEMO_CODE); }
async function tryCode(code) {
  const r = await fetch('/api/check?code=' + encodeURIComponent(code));
  return r.ok;
}
(async () => {
  const gate = document.getElementById('gate');
  const err = document.getElementById('gate-err');
  if (DEMO_CODE && await tryCode(DEMO_CODE)) { gate.hidden = true; }
  document.getElementById('gate-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const code = document.getElementById('gate-code').value.trim();
    err.textContent = 'Checking...';
    if (await tryCode(code)) {
      DEMO_CODE = code;
      try { sessionStorage.setItem('jevDemoCode', code); } catch (e2) {}
      gate.hidden = true; err.textContent = '';
    } else { err.textContent = 'That passcode is not right. Ask the Camp Run team.'; }
  });
})();
</script>
"""
anchor = '<div class="wrap">'  # live.html has no explicit <body>; the gate goes right before the app
assert anchor in page, "no wrap anchor"
page = page.replace(anchor, gate + anchor, 1)
open(os.path.join(OUT, "race", "index.html"), "w", encoding="utf-8").write(page)

items = [{k: it[k] for k in ("id", "src", "branch", "text")} for it in load_items(200)]
with open(os.path.join(OUT, "api", "_items.js"), "w", encoding="utf-8") as fh:
    fh.write("// Fictional Suki Mart complaints (Camp Run sandbox), exported for the sample endpoint.\n")
    fh.write("export default " + json.dumps(items, ensure_ascii=False) + ";\n")
print("built", OUT, len(page) // 1024, "KB page,", len(items), "items")
