"""Build index.html: template.html + data.json (+ Hermes's full Suki Pulse run). No network, no keys."""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "data.json"), encoding="utf-8") as fh:
    data = json.load(fh)

full = os.path.join(HERE, "..", "suki-pulse-site", "data.json")
if os.path.exists(full):
    with open(full, encoding="utf-8") as fh:
        f = json.load(fh)
    data["full_run"] = {k: f[k] for k in ("items_triaged", "seconds", "input_tokens", "cost_usd", "fallbacks")}
    data["full_run"]["items"] = data["full_run"].pop("items_triaged")

with open(os.path.join(HERE, "template.html"), encoding="utf-8") as fh:
    page = fh.read()
blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
out = page.replace("/*DATA*/", blob, 1)
assert "/*DATA*/" not in out, "placeholder not replaced"
dest = os.path.join(HERE, "index.html")
with open(dest, "w", encoding="utf-8") as fh:
    fh.write(out)
print(f"wrote {dest} ({len(out) // 1024} KB)")
if len(sys.argv) > 1:  # optional copy target (the artifact publish path)
    shutil.copyfile(dest, sys.argv[1])
    print(f"copied to {sys.argv[1]}")
