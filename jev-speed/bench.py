"""Jev speed benchmark on real Suki Mart complaints.

Measures, on the same complaints and the same questions Suki Pulse asks:
  1. Jev sequential latency (one call per complaint, 8 questions per call)
  2. Claude Haiku 4.5 (via OpenCode Zen) sequential latency, same questions as JSON
  3. Jev latency as the number of questions per call grows (1 -> 16)
  4. Jev throughput with 8 calls in flight

Keys are read at runtime and never printed or written:
  TypeSafe: C:/dev/.secrets/devcon-typesafe-jev.key (or TYPESAFE_API_KEY)
  Zen:      OPENCODE_ZEN_API_KEY in %LOCALAPPDATA%/hermes/.env (or the env var)

Usage:  python bench.py --probe      # 1 call each, prints timings only
        python bench.py              # full run, writes data.json
"""
import json
import os
import random
import re
import sqlite3
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "Camp-Run-with-Hermes-Agent", "data", "store.db")
JEV_URL = "https://api.typesafe.ai/v1/systemone"
JEV_MODEL = "jev-1.13.0"
ZEN_URL = "https://opencode.ai/zen/v1/messages"
LLM_MODEL = "claude-haiku-4-5"
PRICE = {"jev_in": 0.042, "jev_out": 0.0, "llm_in": 1.00, "llm_out": 5.00}  # USD per 1M tokens

CAUSES = {
    "late_delivery": "The delivery was late, never arrived, or the rider behaved badly.",
    "spoiled_damaged": "An item arrived spoiled, expired, damaged, or not fresh.",
    "out_of_stock": "An item was missing, out of stock, substituted, or the wrong item was sent.",
    "loyalty": "Loyalty / Suki card points are missing, wrong, or expired unfairly.",
    "promo": "A promo or discount code did not work or was not applied.",
    "payment_refund": "A payment failed, the customer was double-charged, or wants a refund.",
}
EXTRA = {  # only used for the question-scaling test
    "mentions_rider": "Does the customer mention the rider or delivery person?",
    "wants_callback": "Does the customer ask to be contacted or called back?",
    "mentions_price": "Does the customer complain about prices or being overcharged?",
    "mentions_app": "Does the customer mention the app or website?",
    "mentions_staff": "Does the customer mention store staff?",
    "mentions_cleanliness": "Does the customer mention cleanliness?",
    "positive_tone": "Is the overall tone of the message positive?",
    "repeat_issue": "Does the customer say this happened before?",
}


def read_keys() -> tuple[str, str]:
    jev = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not jev:
        with open("C:/dev/.secrets/devcon-typesafe-jev.key", encoding="utf-8") as fh:
            jev = fh.read().strip()
    zen = os.environ.get("OPENCODE_ZEN_API_KEY", "").strip()
    if not zen:
        env_path = os.path.join(os.environ["LOCALAPPDATA"], "hermes", ".env")
        with open(env_path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("OPENCODE_ZEN_API_KEY="):
                    zen = line.split("=", 1)[1].strip()
    if not jev or not zen:
        sys.exit("missing TypeSafe or Zen key")
    return jev, zen


def load_items(n: int) -> list[dict]:
    con = sqlite3.connect(f"file:{os.path.abspath(DB)}?mode=ro", uri=True)
    rows = con.execute(
        """SELECT * FROM (
             SELECT 'ticket' AS src, t.id, b.code AS branch, t.subject || '. ' || t.description AS text, t.created_at
             FROM support_tickets t JOIN branches b ON b.id = t.branch_id WHERE t.status IN ('open','pending')
             UNION ALL
             SELECT 'review', r.id, b.code, COALESCE(r.title, '') || '. ' || r.body, r.created_at
             FROM reviews r JOIN branches b ON b.id = r.branch_id WHERE r.rating <= 2 AND r.replied_at IS NULL
           ) ORDER BY created_at DESC LIMIT ?""", (n,)).fetchall()
    return [{"src": s, "id": i, "branch": b, "text": t} for s, i, b, t, _ in rows]


def jev_questions(n_extra: int = 0, only: int | None = None) -> dict:
    qs = {k: {"type": "noul", "instructions": f"Does the customer complain about this? {v}"} for k, v in CAUSES.items()}
    qs["churn_risk"] = {"type": "score", "instructions": "How likely is this customer to stop shopping at Suki Mart?",
                        "criteria": ["Low: mild, likely to stay", "Medium: annoyed, could leave",
                                     "High: angry, threatening to leave or already gone"]}
    qs["urgent"] = {"type": "noul", "instructions": "Does this need a same-day response (money lost, food safety, angry customer)?"}
    for k in list(EXTRA)[:n_extra]:
        qs[k] = {"type": "noul", "instructions": EXTRA[k]}
    if only is not None:
        qs = dict(list(qs.items())[:only])
    return qs


def state_of(item: dict) -> str:
    return f"Suki Mart (Philippine grocery) {item['src']} #{item['id']}. Customer wrote: {item['text']}"


def post(url: str, headers: dict, body: dict, timeout: float = 60) -> tuple[dict, float]:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "jev-speed-bench/1.0",
                                          **headers})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return data, (time.perf_counter() - t0) * 1000


def call_jev(key: str, item: dict, questions: dict) -> dict:
    data, ms = post(JEV_URL, {"Authorization": f"Bearer {key}"},
                    {"model": JEV_MODEL, "state": state_of(item), "questions": questions})
    ans = data["answers"]
    causes = {c: float(ans[c]["noul"]) for c in CAUSES if c in ans}
    return {"ms": round(ms, 1), "tokens_in": int(data.get("usage", {}).get("input_tokens", 0)), "tokens_out": 0,
            "top": max(causes, key=causes.get) if causes else None}


LLM_SYSTEM = (
    "You classify Suki Mart (Philippine grocery chain) customer complaints. Reply with ONLY a JSON object, no prose: "
    '{"late_delivery": p, "spoiled_damaged": p, "out_of_stock": p, "loyalty": p, "promo": p, "payment_refund": p, '
    '"churn_risk": 0|1|2, "urgent": p} where each p is the probability (0 to 1) that the complaint is about that cause. '
    "Causes: " + " ".join(f"{k}: {v}" for k, v in CAUSES.items()) +
    " churn_risk: 0 low, 1 medium, 2 high. urgent: needs a same-day response (money lost, food safety, angry customer)."
)


def call_llm(key: str, item: dict) -> dict:
    data, ms = post(ZEN_URL, {"x-api-key": key, "anthropic-version": "2023-06-01"},
                    {"model": LLM_MODEL, "max_tokens": 200, "system": LLM_SYSTEM,
                     "messages": [{"role": "user", "content": state_of(item)}]})
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    top = None
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            parsed = json.loads(m.group(0))
            causes = {c: float(parsed.get(c, 0) or 0) for c in CAUSES}
            top = max(causes, key=causes.get)
        except (ValueError, TypeError):
            pass
    usage = data.get("usage", {})
    return {"ms": round(ms, 1), "tokens_in": int(usage.get("input_tokens", 0)),
            "tokens_out": int(usage.get("output_tokens", 0)), "top": top}


def retry(fn, *args, tries: int = 3):
    for attempt in range(tries):
        try:
            return fn(*args)
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError) as exc:
            if attempt == tries - 1:
                return {"error": type(exc).__name__}
            time.sleep(1.5 * (attempt + 1))


def sequential(fn, key: str, items: list[dict], label: str) -> list[dict]:
    out, t_run = [], time.perf_counter()
    for i, it in enumerate(items):
        start = (time.perf_counter() - t_run) * 1000
        r = retry(fn, key, it) if fn is call_llm else retry(fn, key, it, jev_questions())
        r.update({"i": i, "start_ms": round(start, 1)})
        out.append(r)
        print(f"  {label} {i + 1}/{len(items)} {r.get('ms', r.get('error'))}", flush=True)
    return out


def pct(values: list[float], p: float) -> float:
    s = sorted(values)
    return round(s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))], 1)


def summarize(rows: list[dict], kind: str) -> dict:
    ok = [r for r in rows if "ms" in r]
    ms = [r["ms"] for r in ok]
    tin, tout = sum(r["tokens_in"] for r in ok), sum(r["tokens_out"] for r in ok)
    cost = (tin * PRICE[f"{kind}_in"] + tout * PRICE[f"{kind}_out"]) / 1e6
    return {"n": len(ok), "errors": len(rows) - len(ok), "p50": pct(ms, 50), "p95": pct(ms, 95),
            "mean": round(statistics.mean(ms), 1), "min": min(ms), "max": max(ms),
            "total_ms": round(sum(ms), 1), "tokens_in": tin, "tokens_out": tout,
            "cost_usd": round(cost, 6), "cost_per_call": round(cost / len(ok), 8)}


def run_burst(call, items: list[dict], workers: int = 8) -> dict:
    """All items with `workers` calls in flight; start/end offsets per call."""
    t0 = time.perf_counter()

    def timed(it):
        s = (time.perf_counter() - t0) * 1000
        r = retry(call, it)
        return {"start_ms": round(s, 1), "end_ms": round((time.perf_counter() - t0) * 1000, 1), "ok": "ms" in r}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(timed, items))
    wall = (time.perf_counter() - t0) * 1000
    return {"concurrency": workers, "n": len(rows), "ok": sum(r["ok"] for r in rows), "wall_ms": round(wall, 1),
            "per_sec": round(len(rows) / (wall / 1000), 2), "rows": rows}


def main() -> None:
    jev_key, zen_key = read_keys()
    if "--jev-timing" in sys.argv:  # which timing fields does Jev return? (no keys printed)
        it = load_items(1)[0]
        req = urllib.request.Request(JEV_URL, method="POST", data=json.dumps(
            {"model": JEV_MODEL, "state": state_of(it), "questions": jev_questions()}).encode(), headers={
            "Content-Type": "application/json", "User-Agent": "jev-speed-bench/1.0", "Authorization": f"Bearer {jev_key}"})
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=60) as resp:
            body, hdrs = json.loads(resp.read()), dict(resp.headers)
        print("client ms:", round((time.perf_counter() - t0) * 1000, 1))
        print("body keys:", list(body), "| usage:", body.get("usage"))
        print("timing-like headers:", {k: v for k, v in hdrs.items() if re.search(r"time|timing|latency|duration|ms|region|served|cf-ray", k, re.I)})
        print("timing-like body fields:", {k: v for k, v in body.items() if re.search(r"time|latency|duration|ms", k, re.I)})
        return
    if "--haiku-burst" in sys.argv:  # fairness: Haiku with 8 in flight too, merged into data.json
        path = os.path.join(HERE, "data.json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        items = load_items(len(data["items"]))
        data["burst_llm"] = run_burst(lambda it: call_llm(zen_key, it), items)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1)
        print("haiku burst:", {k: v for k, v in data["burst_llm"].items() if k != "rows"})
        return
    if "--probe" in sys.argv:
        it = load_items(1)[0]
        for label, fn in (("jev", lambda: call_jev(jev_key, it, jev_questions())), ("haiku", lambda: call_llm(zen_key, it))):
            try:
                print(f"{label}:", fn())
            except urllib.error.HTTPError as exc:
                print(f"{label}: HTTP {exc.code} {exc.read()[:200]!r}")
        return

    n = 40
    items = load_items(n)
    print(f"{len(items)} complaints loaded")
    retry(call_jev, jev_key, items[0], jev_questions())  # warm-up, not recorded
    retry(call_llm, zen_key, items[0])

    print("1/4 jev sequential")
    jev_seq = sequential(call_jev, jev_key, items, "jev")
    print("2/4 haiku sequential")
    llm_seq = sequential(call_llm, zen_key, items, "haiku")

    print("3/4 question scaling")
    counts, sample = [1, 2, 4, 8, 16], items[:6]
    plan = [(c, it) for it in sample for c in counts]
    random.Random(7).shuffle(plan)
    scaling = {c: [] for c in counts}
    for c, it in plan:
        qs = jev_questions(n_extra=max(0, c - 8), only=c if c < 8 else None)
        r = retry(call_jev, jev_key, it, qs)
        if "ms" in r:
            scaling[c].append({"ms": r["ms"], "tokens_in": r["tokens_in"]})

    print("4/4 burst x8")
    t0 = time.perf_counter()

    def timed(it):
        s = (time.perf_counter() - t0) * 1000
        r = retry(call_jev, jev_key, it, jev_questions())
        return {"start_ms": round(s, 1), "end_ms": round((time.perf_counter() - t0) * 1000, 1), "ok": "ms" in r}

    with ThreadPoolExecutor(max_workers=8) as pool:
        burst_rows = list(pool.map(timed, items))
    burst_wall = (time.perf_counter() - t0) * 1000

    agree = [a["top"] == b["top"] for a, b in zip(jev_seq, llm_seq) if a.get("top") and b.get("top")]
    data = {
        "measured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "where": "rieLaptop, Avtica office, Makati (each call includes a fresh HTTPS connection)",
        "models": {"jev": JEV_MODEL, "llm": f"{LLM_MODEL} via OpenCode Zen"},
        "questions_per_call": 8, "prices_per_mtok": PRICE,
        "items": [{"i": i, "src": it["src"], "id": it["id"], "branch": it["branch"], "text": it["text"][:110],
                   "jev_top": jev_seq[i].get("top"), "llm_top": llm_seq[i].get("top")} for i, it in enumerate(items)],
        "jev_seq": jev_seq, "llm_seq": llm_seq,
        "summary": {"jev": summarize(jev_seq, "jev"), "llm": summarize(llm_seq, "llm"),
                    "top_cause_agreement": round(sum(agree) / len(agree), 3) if agree else None},
        "scaling": [{"questions": c, "p50": pct([x["ms"] for x in v], 50) if v else None,
                     "samples": [x["ms"] for x in v],
                     "tokens_in_avg": round(statistics.mean([x["tokens_in"] for x in v])) if v else None}
                    for c, v in scaling.items()],
        "burst": {"concurrency": 8, "n": len(burst_rows), "ok": sum(r["ok"] for r in burst_rows),
                  "wall_ms": round(burst_wall, 1), "per_sec": round(len(burst_rows) / (burst_wall / 1000), 2),
                  "rows": burst_rows},
    }
    with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    s = data["summary"]
    print(f"jev p50 {s['jev']['p50']} ms, haiku p50 {s['llm']['p50']} ms, "
          f"cost jev ${s['jev']['cost_usd']} haiku ${s['llm']['cost_usd']}, burst {data['burst']['per_sec']}/s")


if __name__ == "__main__":
    main()
