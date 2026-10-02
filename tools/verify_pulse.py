"""Read-only checks of assumptions in Suki Pulse server.py against the live store.db."""
import sqlite3

DB = r"C:\dev\devcon\hermes-hackathon\Camp-Run-with-Hermes-Agent\data\store.db"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
q = lambda s: con.execute(s).fetchall()  # noqa: E731

print("txn_type values:", q("SELECT DISTINCT txn_type FROM loyalty_transactions"))
print("loyalty_transactions DDL:", q("SELECT sql FROM sqlite_master WHERE name='loyalty_transactions'")[0][0][:400])
print("purchase_orders DDL:", q("SELECT sql FROM sqlite_master WHERE name='purchase_orders'")[0][0][:500])
print("po_number count/max/min:", q("SELECT COUNT(*), MAX(po_number), MIN(po_number) FROM purchase_orders"))
print("indexes on purchase_orders:", q("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='purchase_orders'"))
print("branch codes:", [r[0] + "=" + r[1] for r in q("SELECT code, name FROM branches ORDER BY code")])
print("live tables include jev_triage/pulse_actions:",
      q("SELECT name FROM sqlite_master WHERE name IN ('jev_triage','pulse_actions')"))
print("support_tickets status CHECK:", "CHECK" in q("SELECT sql FROM sqlite_master WHERE name='support_tickets'")[0][0])
