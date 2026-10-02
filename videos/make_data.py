"""Build videos/suki-data.json from the real Jev run (dashboard data.json) plus read-only store.db queries.
Re-run after a live fix run: fix_run is filled from pulse_actions and a fresh scorecard when rows exist."""
import json
import sqlite3

ROOT = "C:/dev/devcon/hermes-hackathon"
try:  # previous snapshot: live values survive a seed.py reset
    prev = json.load(open(f"{ROOT}/videos/suki-data.json", encoding="utf-8"))
except (OSError, ValueError):
    prev = {}
NOW = "2026-09-30 21:00:00"
site = json.load(open(f"{ROOT}/suki-pulse-site/data.json", encoding="utf-8"))
c = sqlite3.connect(f"file:{ROOT}/Camp-Run-with-Hermes-Agent/data/store.db?mode=ro", uri=True)
c.row_factory = sqlite3.Row


def q(sql, p=()):
    return [dict(r) for r in c.execute(sql, p)]


def one(sql, p):
    return list(q(sql, p)[0].values())[0]


BID, CODE = 7, "TMR"
OPEN_PO = "('pending','in_transit','partially_received')"


def scorecard():
    return {
        "open_tickets": one("SELECT COUNT(*) FROM support_tickets WHERE branch_id=? AND status IN ('open','pending')", (BID,)),
        "never_answered": one("SELECT COUNT(*) FROM support_tickets WHERE branch_id=? AND status IN ('open','pending') AND first_response_at IS NULL", (BID,)),
        "unreplied_low_reviews": one("SELECT COUNT(*) FROM reviews WHERE branch_id=? AND rating<=2 AND replied_at IS NULL", (BID,)),
        "loyalty_mismatches": one(
            """SELECT COUNT(*) FROM loyalty_accounts a JOIN customers c ON c.id=a.customer_id
               WHERE c.home_branch_id=? AND a.points_balance != (SELECT COALESCE(SUM(points),0)
               FROM loyalty_transactions t WHERE t.loyalty_account_id=a.id)""", (BID,)),
        "reorder_without_po": one(
            f"""SELECT COUNT(*) FROM inventory i WHERE i.branch_id=? AND i.on_hand<=i.reorder_point
                AND NOT EXISTS (SELECT 1 FROM purchase_orders p WHERE p.branch_id=i.branch_id
                AND p.product_id=i.product_id AND p.status IN {OPEN_PO})""", (BID,)),
    }


loyal = q("""SELECT c.id AS customer_id, c.first_name || ' ' || substr(c.last_name,1,1) || '.' AS customer, a.tier,
          a.points_balance AS stored, x.ledger, x.ledger - a.points_balance AS diff
   FROM loyalty_accounts a JOIN customers c ON c.id = a.customer_id
   JOIN (SELECT loyalty_account_id, SUM(points) AS ledger FROM loyalty_transactions GROUP BY loyalty_account_id) x
     ON x.loyalty_account_id = a.id
   WHERE c.home_branch_id = ? AND a.points_balance != x.ledger ORDER BY ABS(x.ledger - a.points_balance) DESC LIMIT 3""", (BID,))
restock = q(f"""SELECT p.sku, p.name, i.on_hand, i.reorder_point, i.reorder_qty, s.name AS supplier
    FROM inventory i JOIN products p ON p.id = i.product_id JOIN suppliers s ON s.id = p.supplier_id
    WHERE i.branch_id = ? AND i.on_hand <= i.reorder_point
    AND NOT EXISTS (SELECT 1 FROM purchase_orders po WHERE po.branch_id = i.branch_id AND po.product_id = i.product_id
    AND po.status IN {OPEN_PO})
    ORDER BY (i.on_hand * 1.0 / MAX(i.avg_daily_sales, 0.1)) ASC LIMIT 3""", (BID,))

t = next(b for b in site["branches"] if b["code"] == CODE)
tot = {}
for b in site["branches"]:
    for k, v in b["causes"].items():
        tot[k] = tot.get(k, 0) + v

# Real fix run, if one has happened on the live DB.
try:
    acts = q("SELECT action, target, detail FROM pulse_actions WHERE branch_code=? ORDER BY id", (CODE,))
except sqlite3.OperationalError:
    acts = []

placeholder_fix = {
    "placeholder": True,
    "source": "Projection in the format of SKILL.md's example output. Re-run make_data.py after the live fix run to swap in pulse_actions rows and a fresh scorecard.",
    "actions": [
        {"tool": "flag_rider_for_coaching", "target": "Christian Lacson", "result": "flagged: 63 late of 85 in 30 days"},
        {"tool": "draft_purchase_orders", "target": "TMR, 2 items", "result": "2 POs drafted at real supplier lead time"},
        {"tool": "fix_loyalty_balance", "target": loyal[0]["customer"] if loyal else "top mismatch", "result": "ledger reconciled in the customer's favor"},
        {"tool": "resolve_ticket", "target": "TKT-00585", "result": "resolved with note"},
        {"tool": "reply_to_review", "target": "review #3036", "result": "reply posted"},
    ],
    "reply": "Pasensya na po sa late delivery at sa natunaw na ice cream. We flagged the rider for coaching and added goodwill points to your Suki card.",
    "scorecard_after": {"open_tickets": 14, "never_answered": 2, "unreplied_low_reviews": 21, "loyalty_mismatches": 5, "reorder_without_po": 20},
}
if acts:
    replies = q("SELECT reply_text FROM reviews WHERE branch_id=? AND reply_text IS NOT NULL ORDER BY replied_at DESC LIMIT 1", (BID,))
    fix = {
        "placeholder": False,
        "source": "pulse_actions rows and a fresh scorecard from the live store.db",
        "actions": [{"tool": a["action"], "target": a["target"], "result": (a["detail"] or "")[:90]} for a in acts],
        "reply": replies[0]["reply_text"] if replies else placeholder_fix["reply"],
        "scorecard_after": scorecard(),
    }
elif prev.get("fix_run", {}).get("placeholder") is False:
    fix = prev["fix_run"]  # keep a captured real run after seed.py wipes pulse_actions
else:
    fix = placeholder_fix
fix["prompt"] = "Use the suki-pulse skill: fix the top root cause at branch TMR. Show the plan and ask before writing."

labels = {"late_delivery": "Late delivery", "spoiled_damaged": "Spoiled / damaged", "out_of_stock": "Out of stock / wrong",
          "loyalty": "Loyalty points", "promo": "Promo code", "payment_refund": "Payment / refund"}


def live_pulse():
    """The live demo's pulse check: what the ::suki-pulse card showed (jev_triage rows for TMR)."""
    try:
        rows = q("SELECT source, item_id, causes, churn_risk, urgent, engine, input_tokens FROM jev_triage WHERE branch_id=?", (BID,))
    except sqlite3.OperationalError:
        return None
    if not rows:
        return None
    counts = {k: 0 for k in labels}
    for r in rows:
        for k, p in json.loads(r["causes"]).items():
            if p >= 0.5:
                counts[k] += 1
    tokens = sum(r["input_tokens"] for r in rows)
    feat = next((r for r in rows if (r["source"], r["item_id"]) == ("ticket", 585)), None)
    return {
        "items": len(rows), "engine": sorted({r["engine"] for r in rows}), "input_tokens": tokens,
        "cost_usd": round(tokens * 0.042 / 1_000_000, 6),
        "cause_counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
        "high_churn": sum(1 for r in rows if (r["churn_risk"] or 0) >= 1.5),
        "featured": feat and {"ref": "TKT-00585", "text": "My order came 97 minutes late and the frozen items were soft.",
                              "causes": json.loads(feat["causes"]), "churn_risk": feat["churn_risk"],
                              "urgent": feat["urgent"], "input_tokens": feat["input_tokens"]},
    }


def jev_race():
    """Measured Jev vs Claude Haiku 4.5 benchmark (jev-speed/data.json, reviewer session)."""
    try:
        b = json.load(open(f"{ROOT}/jev-speed/data.json", encoding="utf-8"))
    except (OSError, ValueError):
        return None
    j, l = b["summary"]["jev"], b["summary"]["llm"]
    jf = sorted(round((r["start_ms"] + r["ms"]) / 1000, 3) for r in b["jev_seq"])
    lf = sorted(round((r["start_ms"] + r["ms"]) / 1000, 3) for r in b["llm_seq"])
    return {
        "measured_at": b["measured_at_utc"], "where": "rieLaptop at the venue",
        "jev_model": b["models"]["jev"], "llm_model": "Claude Haiku 4.5",
        "n": len(jf), "questions_per_call": b["questions_per_call"],
        "jev_finish_s": jf, "llm_finish_s": lf,
        "llm_done_when_jev_done": sum(1 for t in lf if t <= jf[-1]),
        "p50_ms": {"jev": j["p50"], "llm": l["p50"]}, "p95_ms": {"jev": j["p95"], "llm": l["p95"]},
        "total_s": {"jev": round(j["total_ms"] / 1000, 1), "llm": round(l["total_ms"] / 1000, 1)},
        "cost_per_call": {"jev": j["cost_per_call"], "llm": l["cost_per_call"]},
        "speedup_p50": round(l["p50"] / j["p50"], 1),
        "cost_ratio": round(l["cost_per_call"] / j["cost_per_call"]),
        "agreement": b["summary"]["top_cause_agreement"],
        "burst": {"concurrency": b["burst"]["concurrency"], "jev_s": round(b["burst"]["wall_ms"] / 1000, 1),
                  "llm_s": round(b["burst_llm"]["wall_ms"] / 1000, 1)},
    }


data = {
    "_about": "Real values for the Suki Pulse video drafts. Sources: suki-pulse-site/data.json (real Jev run at sandbox time 2026-09-30 21:00) and read-only store.db queries. fix_run.placeholder says whether the fix run is real yet.",
    "product": "Suki Pulse",
    "tagline": "complaint \u2192 root cause \u2192 fix",
    "badge": "Camp Run \u00b7 Open Innovation",
    "pitch": "Every complaint at Suki Mart is a symptom. Suki Pulse lets Hermes find the operational cause behind it (a late rider, a supplier, a missing purchase order, a broken points ledger) and fix both sides.",
    "why": "Jev is the fast classifier: it read all of the open complaints in about a minute, for less than two cents. Hermes is the slow thinker: it reads the evidence, decides on the fixes, asks you, and then acts through the MCP tools.",
    "credits": "Hermes Agent \u00b7 TypeSafe Jev \u00b7 DEVCON \u00d7 Avtica \u00b7 Oct 2 2026",
    "url": "suki-pulse.vercel.app",
    "brand": {"bg": "#070d2a", "surface": "#0d1640", "line": "#1f2b66", "ink": "#eef2ff", "muted": "#9aa6cf", "faint": "#5d6a99",
              "accent": "#f6e27a", "cyan": "#5ad1f2", "danger": "#ff8a7a", "sans": "IBM Plex Sans", "mono": "IBM Plex Mono"},
    "cause_labels": labels,
    "jev_run": {"engine": site["engine"][0], "items": site["items_triaged"], "branches": len(site["branches"]),
                "input_tokens": site["input_tokens"], "cost_usd": site["cost_usd"], "seconds": site["seconds"],
                "fallbacks": site["fallbacks"], "high_churn": sum(b["high_churn"] for b in site["branches"]),
                "causes_total": dict(sorted(tot.items(), key=lambda kv: -kv[1]))},
    "jev_single_call": {"seconds": 0.61, "input_tokens": 462, "cost_usd": 0.00002},
    "heatmap": [{"code": b["code"], "name": b["name"].replace("Suki Mart ", ""), "causes": b["causes"], "open": b["items"],
                 "high_churn": b["high_churn"], "top_cause": b["top_cause"]} for b in site["branches"]],
    "branch": {"code": CODE, "name": "Tomas Morato", "items": t["items"], "high_churn": t["high_churn"], "top_cause": t["top_cause"],
               "causes": t["causes"],
               "scorecard_before": {k: v for k, v in t["scorecard"].items() if k not in ("branch", "pulse_actions_taken")},
               "rider": {**t["worst_rider"], "days": 30},  # root_cause_rollup window "restock_top": t["most_urgent_restock"], "jev_samples": t["sample"],
               "loyalty_mismatch_top": loyal, "reorder_without_po_top": restock},
    "complaints": [
        {"ref": "TKT-00585", "kind": "ticket", "priority": "high", "text": "My order came 97 minutes late and the frozen items were soft."},
        {"ref": "review #3036", "kind": "review", "stars": 2, "text": "Delivery was more than an hour late. Ice cream melted."},
        {"ref": "review #1644", "kind": "review", "stars": 1, "text": "Not again. Out of stock again. Third time this week."},
        {"ref": "review #270", "kind": "review", "stars": 1, "text": "Disappointed. My points disappeared. Customer service never replied."},
        {"ref": "review #959", "kind": "review", "stars": 2, "text": "Please fix this. App crashed at checkout and I was charged twice."},
        {"ref": "TKT-01416", "kind": "ticket", "priority": "low", "text": "Promo SUKI100 applied the wrong amount."},
        {"ref": "review #2544", "kind": "review", "stars": 1, "text": "Please fix this. Bread was stale when I bought it."},
    ],
    "layers": [  # v2 site copy, "How Hermes runs it"
        {"n": "1", "name": "Desktop plugin", "code": "", "body": "A Suki Pulse pane in Hermes Desktop. Pick a branch, then run a pulse check, fix the top cause, or recover the riskiest customer. Results come back as native cards in the chat."},
        {"n": "2", "name": "Skill", "code": "suki-pulse", "body": "Triage, then root cause, then a plan that covers operations and customers. It asks before it writes, then shows the before and after."},
        {"n": "3", "name": "MCP server", "code": "suki", "body": "Ten domain tools. Triage, rollup, scorecard and customer story read. Resolve, reply, reconcile points, draft POs and flag a rider write."},
        {"n": "4", "name": "TypeSafe Jev", "code": "", "body": "One call per complaint returns six yes or no cause checks, a churn score and urgency. Cached, fractions of a cent, with a keyword fallback."},
    ],
    "pane_buttons": ["Pulse check", "Fix top root cause", "Recover riskiest customer", "Branch scorecard"],
    "live_pulse": live_pulse() or prev.get("live_pulse"),
    "jev_race": jev_race() or prev.get("jev_race"),
    "fix_run": fix,
}
out = f"{ROOT}/videos/suki-data.json"
open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1, ensure_ascii=False))
# The canvas film loads data through a script tag (file:// cannot fetch JSON).
open(f"{ROOT}/videos/suki-data.js", "w", encoding="utf-8").write("window.SUKI = " + json.dumps(data, ensure_ascii=False) + ";\n")
assert "\u2014" not in json.dumps(data, ensure_ascii=False), "em dash in data"
print("wrote", out, "| fix_run placeholder:", fix["placeholder"], "| loyalty top:", loyal[:1], "| restock:", [r["name"] for r in restock])
