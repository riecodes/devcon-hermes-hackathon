"""Read-only: does root_cause_rollup's promo query miss SEPT3X (budget 0.0, not NULL)?"""
import sqlite3

c = sqlite3.connect("file:C:/dev/devcon/hermes-hackathon/Camp-Run-with-Hermes-Agent/data/store.db?mode=ro", uri=True)
JOIN = "FROM orders o JOIN promos pr ON pr.id = o.promo_id JOIN branches b ON b.id = o.branch_id"
print("SEPT3X budget_php:", c.execute("SELECT budget_php, typeof(budget_php) FROM promos WHERE code='SEPT3X'").fetchall())
print("current query (IS NULL), TMR:",
      c.execute(f"SELECT COUNT(*) {JOIN} WHERE b.code='TMR' AND pr.budget_php IS NULL AND o.discount = 0").fetchone()[0])
print("fixed query (COALESCE = 0), TMR:",
      c.execute(f"SELECT pr.code, COUNT(*) {JOIN} WHERE b.code='TMR' AND COALESCE(pr.budget_php, 0) = 0 "
                "AND o.discount = 0 GROUP BY pr.code").fetchall())
print("fixed query, all branches:",
      c.execute(f"SELECT COUNT(*) {JOIN} WHERE COALESCE(pr.budget_php, 0) = 0 AND o.discount = 0").fetchone()[0])
