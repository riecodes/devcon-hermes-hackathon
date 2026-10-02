"""Read-only fact sheet for the pitch, from the freshly reset Suki Mart store.db."""
import sqlite3

DB = r"C:\dev\devcon\hermes-hackathon\Camp-Run-with-Hermes-Agent\data\store.db"
NOW = "2026-09-30 21:00:00"
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
one = lambda sql, p=(): c.execute(sql, p).fetchone()[0]  # noqa: E731
rows = lambda sql, p=(): c.execute(sql, p).fetchall()  # noqa: E731

tables = [r[0] for r in rows("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
counts = {t: one(f"SELECT COUNT(*) FROM {t}") for t in tables}
print("tables:", len(tables), "| data tables (excl. sandbox_info):", len([t for t in tables if t != "sandbox_info"]))
print("total rows:", f"{sum(counts.values()):,}")
print("biggest:", sorted(counts.items(), key=lambda kv: -kv[1])[:5])
print("history:", one("SELECT MIN(created_at) FROM orders"), "to", one("SELECT MAX(created_at) FROM orders"))
sales = one("SELECT ROUND(SUM(total)) FROM orders WHERE status='completed'")
print("6-month sales (completed orders, PHP):", f"{sales:,.0f}")

print("\n-- tickets")
print("open/pending:", one("SELECT COUNT(*) FROM support_tickets WHERE status IN ('open','pending')"))
print("avg age days:", one("SELECT ROUND(AVG(julianday(?) - julianday(created_at)),1) FROM support_tickets WHERE status IN ('open','pending')", (NOW,)))
print("oldest open days:", one("SELECT ROUND(MAX(julianday(?) - julianday(created_at)),0) FROM support_tickets WHERE status IN ('open','pending')", (NOW,)))
print("never answered:", one("SELECT COUNT(*) FROM support_tickets WHERE status IN ('open','pending') AND first_response_at IS NULL"))
print("urgent still open:", one("SELECT COUNT(*) FROM support_tickets WHERE status IN ('open','pending') AND priority='urgent'"))

print("\n-- reviews")
print("unreplied 1-2 star:", one("SELECT COUNT(*) FROM reviews WHERE rating <= 2 AND replied_at IS NULL"))
print("open tickets + unreplied low reviews:", one("SELECT (SELECT COUNT(*) FROM support_tickets WHERE status IN ('open','pending')) + (SELECT COUNT(*) FROM reviews WHERE rating<=2 AND replied_at IS NULL)"))
print("top low-review topics:", rows("SELECT topic, COUNT(*) FROM reviews WHERE rating<=2 GROUP BY topic ORDER BY 2 DESC LIMIT 3"))

print("\n-- delivery")
print("chain late %:", one("SELECT ROUND(100.0*AVG(delivered_at > promised_by),1) FROM deliveries WHERE delivered_at IS NOT NULL"))
print("TMR late % all-time:", one("SELECT ROUND(100.0*AVG(d.delivered_at > d.promised_by),1) FROM deliveries d JOIN branches b ON b.id=d.branch_id WHERE b.code='TMR' AND d.delivered_at IS NOT NULL"))
print("TMR late % last 30d:", one("SELECT ROUND(100.0*AVG(d.delivered_at > d.promised_by),1) FROM deliveries d JOIN branches b ON b.id=d.branch_id WHERE b.code='TMR' AND d.delivered_at IS NOT NULL AND d.delivered_at >= datetime(?, '-30 days')", (NOW,)))
print("worst rider 30d:", rows("""SELECT r.first_name||' '||r.last_name, SUM(d.delivered_at > d.promised_by) late, COUNT(*) n, COUNT(DISTINCT d.branch_id) br
  FROM deliveries d JOIN riders r ON r.id=d.rider_id WHERE d.delivered_at IS NOT NULL AND d.delivered_at >= datetime(?, '-30 days')
  GROUP BY r.id ORDER BY late DESC LIMIT 1""", (NOW,)))

print("\n-- stock & suppliers")
print("at/below reorder, no open PO:", one("""SELECT COUNT(*) FROM inventory i WHERE i.on_hand <= i.reorder_point AND NOT EXISTS (SELECT 1 FROM purchase_orders p
  WHERE p.branch_id=i.branch_id AND p.product_id=i.product_id AND p.status IN ('pending','in_transit','partially_received'))"""))
print("zero stock items:", one("SELECT COUNT(*) FROM inventory WHERE on_hand = 0"))
expiring = one("SELECT ROUND(SUM(i.on_hand*p.cost_price)) FROM inventory i JOIN products p ON p.id=i.product_id "
               "WHERE p.is_perishable=1 AND i.nearest_expiry_date <= datetime(?, '+3 days')", (NOW,))
print("perishables expiring <=3d, PHP at cost:", f"{expiring:,.0f}")
print("worst supplier:", rows("""SELECT s.name, s.promised_lead_time_days, ROUND(AVG(julianday(p.received_at)-julianday(p.ordered_at)),1), ROUND(100.0*AVG(p.received_at > p.expected_at))
  FROM purchase_orders p JOIN suppliers s ON s.id=p.supplier_id WHERE p.received_at IS NOT NULL GROUP BY s.id ORDER BY 4 DESC LIMIT 1"""))

print("\n-- loyalty & promo")
print("ledger mismatches:", one("SELECT COUNT(*) FROM loyalty_accounts a WHERE a.points_balance != (SELECT COALESCE(SUM(points),0) FROM loyalty_transactions t WHERE t.loyalty_account_id=a.id)"))
print("points out of sync (sum |diff|):", one("SELECT SUM(ABS(a.points_balance - (SELECT COALESCE(SUM(points),0) FROM loyalty_transactions t WHERE t.loyalty_account_id=a.id))) FROM loyalty_accounts a"))
print("SEPT3X orders with no budget/discount:", one("SELECT COUNT(*) FROM orders o JOIN promos p ON p.id=o.promo_id WHERE p.code='SEPT3X' AND o.discount=0"))

print("\n-- a REAL customer at TMR: open ticket + unreplied low review + late delivery")
for r in rows("""
  SELECT c.id, c.first_name||' '||c.last_name, t.ticket_number, t.subject, t.category, ROUND(julianday(?) - julianday(t.created_at)) AS age_days,
         t.first_response_at IS NULL AS never_answered, rv.rating, rv.title,
         (SELECT ROUND(MAX((julianday(d.delivered_at)-julianday(d.promised_by))*1440)) FROM deliveries d JOIN orders o ON o.id=d.order_id WHERE o.customer_id=c.id) AS worst_late_min
  FROM customers c
  JOIN support_tickets t ON t.customer_id=c.id AND t.status IN ('open','pending')
  JOIN branches b ON b.id=t.branch_id AND b.code='TMR'
  JOIN reviews rv ON rv.customer_id=c.id AND rv.rating<=2 AND rv.replied_at IS NULL
  ORDER BY never_answered DESC, age_days DESC LIMIT 3""", (NOW,)):
    print(r)
