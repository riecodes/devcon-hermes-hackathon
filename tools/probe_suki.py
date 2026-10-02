"""Read-only probes of the Suki Mart sandbox to surface the planted problems."""
import sqlite3

import os
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Camp-Run-with-Hermes-Agent", "data", "store.db")
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
NOW = "2026-09-30 21:00:00"

def show(title, sql, params=()):
    rows = con.execute(sql, params).fetchall()
    print(f"\n## {title}")
    for r in rows:
        print("  ", " | ".join("" if v is None else str(v) for v in r))

show("sandbox_info", "SELECT key, value FROM sandbox_info")

# --- Business Operations ---
show("Stockout risk: items under 2 days of cover (top branches)",
     """SELECT b.code, COUNT(*) AS items_lt_2d,
               SUM(i.on_hand = 0) AS zero_stock
        FROM inventory i JOIN branches b ON b.id = i.branch_id
        WHERE i.avg_daily_sales > 0 AND i.on_hand * 1.0 / i.avg_daily_sales < 2
        GROUP BY b.code ORDER BY items_lt_2d DESC LIMIT 6""")
show("Below reorder point with NO open PO",
     """SELECT COUNT(*) FROM inventory i
        WHERE i.on_hand <= i.reorder_point AND NOT EXISTS (
          SELECT 1 FROM purchase_orders p WHERE p.branch_id = i.branch_id
          AND p.product_id = i.product_id AND p.status IN ('pending','in_transit','partially_received'))""")
show("Expiring perishables: on hand that expires within 3 days (value at cost)",
     """SELECT b.code, COUNT(*) items, ROUND(SUM(i.on_hand * p.cost_price)) AS php_at_risk
        FROM inventory i JOIN products p ON p.id = i.product_id JOIN branches b ON b.id = i.branch_id
        WHERE i.nearest_expiry_date IS NOT NULL AND i.nearest_expiry_date <= date(?, '+3 day')
        GROUP BY b.code ORDER BY php_at_risk DESC LIMIT 6""", (NOW,))
show("Supplier reliability: promised vs actual lead time, late %, short-shipped %",
     """SELECT s.name, s.promised_lead_time_days AS promised,
               ROUND(AVG(julianday(p.received_at) - julianday(p.ordered_at)), 1) AS actual,
               ROUND(100.0 * AVG(p.received_at > p.expected_at), 0) AS late_pct,
               ROUND(100.0 * AVG(p.received_quantity < p.quantity), 0) AS short_pct,
               COUNT(*) AS pos
        FROM purchase_orders p JOIN suppliers s ON s.id = p.supplier_id
        WHERE p.received_at IS NOT NULL
        GROUP BY s.id ORDER BY late_pct DESC LIMIT 6""")
show("Overdue open POs (expected before today, not received)",
     """SELECT s.name, COUNT(*) AS overdue, MIN(p.expected_at) AS oldest
        FROM purchase_orders p JOIN suppliers s ON s.id = p.supplier_id
        WHERE p.status IN ('pending','in_transit') AND p.expected_at < ?
        GROUP BY s.id ORDER BY overdue DESC LIMIT 5""", (NOW,))
show("Staffing: scheduled next 14 days vs targets is complex; no-show + sick rate by branch (last 8 weeks)",
     """SELECT b.code, COUNT(*) AS shifts,
               ROUND(100.0 * AVG(s.status IN ('no_show','called_in_sick')), 1) AS absent_pct
        FROM shifts s JOIN branches b ON b.id = s.branch_id
        WHERE s.shift_date <= date(?) GROUP BY b.code ORDER BY absent_pct DESC LIMIT 6""", (NOW,))
show("Promos: budget vs discount spent, and margin",
     """SELECT pr.code, pr.promo_type, pr.budget_php,
               ROUND(SUM(o.discount)) AS discount_spent, COUNT(o.id) AS orders,
               pr.starts_on, pr.ends_on
        FROM promos pr LEFT JOIN orders o ON o.promo_id = pr.id AND o.status = 'completed'
        GROUP BY pr.id ORDER BY (discount_spent - COALESCE(pr.budget_php, 0)) DESC LIMIT 6""")
show("Promo used outside its dates (count)",
     """SELECT pr.code, COUNT(*) FROM orders o JOIN promos pr ON pr.id = o.promo_id
        WHERE date(o.created_at) < pr.starts_on OR date(o.created_at) > pr.ends_on
        GROUP BY pr.code ORDER BY 2 DESC LIMIT 5""")
show("Items sold below cost (lines, loss)",
     """SELECT p.name, COUNT(*) AS lines, ROUND(SUM((oi.unit_cost - oi.unit_price) * oi.quantity)) AS loss
        FROM order_items oi JOIN products p ON p.id = oi.product_id
        WHERE oi.unit_price < oi.unit_cost GROUP BY p.id ORDER BY loss DESC LIMIT 5""")

# --- Customer Experience ---
show("Open/pending tickets by priority, with age",
     """SELECT priority, COUNT(*) AS open_n,
               ROUND(AVG(julianday(?) - julianday(created_at)), 1) AS avg_age_days,
               SUM(first_response_at IS NULL) AS no_first_response
        FROM support_tickets WHERE status IN ('open','pending')
        GROUP BY priority ORDER BY open_n DESC""", (NOW,))
show("Ticket categories: volume, avg CSAT, avg hours to resolve",
     """SELECT category, COUNT(*) n, ROUND(AVG(csat_score), 2) csat,
               ROUND(AVG((julianday(resolved_at) - julianday(created_at)) * 24), 1) AS hrs_to_resolve
        FROM support_tickets GROUP BY category ORDER BY csat ASC LIMIT 6""")
show("Reviews: low ratings with no reply, by branch",
     """SELECT b.code, COUNT(*) AS unreplied_1_2_star, ROUND(AVG(r.rating), 2) AS branch_avg
        FROM reviews r JOIN branches b ON b.id = r.branch_id
        WHERE r.rating <= 2 AND r.replied_at IS NULL GROUP BY b.code ORDER BY 2 DESC LIMIT 6""")
show("Review topics driving 1-2 stars",
     """SELECT topic, COUNT(*) FROM reviews WHERE rating <= 2 GROUP BY topic ORDER BY 2 DESC LIMIT 6""")
show("Loyalty: points expiring within 30 days (accounts, points)",
     """SELECT tier, COUNT(*) accounts, SUM(points_expiring) pts
        FROM loyalty_accounts WHERE points_expiring > 0 AND points_expiry_date <= date(?, '+30 day')
        AND status = 'active' GROUP BY tier ORDER BY pts DESC""", (NOW,))
show("Loyalty ledger mismatch: balance vs sum of transactions",
     """SELECT COUNT(*) FROM loyalty_accounts la
        WHERE la.points_balance != (SELECT COALESCE(SUM(points), 0) FROM loyalty_transactions t
                                    WHERE t.loyalty_account_id = la.id)""")
show("Lapsed customers: 3+ orders before, none in last 60 days (win-back pool), opted in",
     """SELECT COUNT(*) FROM customers c
        WHERE c.marketing_opt_in = 1
          AND (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) >= 3
          AND (SELECT MAX(created_at) FROM orders o WHERE o.customer_id = c.id) < date(?, '-60 day')""", (NOW,))
show("Delivery: late % and failure % by branch",
     """SELECT b.code, COUNT(*) n,
               ROUND(100.0 * AVG(d.delivered_at > d.promised_by), 1) AS late_pct,
               ROUND(100.0 * AVG(d.status IN ('failed','returned')), 1) AS fail_pct
        FROM deliveries d JOIN branches b ON b.id = d.branch_id
        GROUP BY b.code ORDER BY late_pct DESC LIMIT 6""")
show("Riders with the most late deliveries (last 30 days)",
     """SELECT r.first_name || ' ' || r.last_name, r.status, r.rating, COUNT(*) AS late
        FROM deliveries d JOIN riders r ON r.id = d.rider_id
        WHERE d.delivered_at > d.promised_by AND d.promised_by >= date(?, '-30 day')
        GROUP BY r.id ORDER BY late DESC LIMIT 5""", (NOW,))
show("Customer data quality: duplicate emails",
     """SELECT COUNT(*) FROM (SELECT lower(email) e FROM customers WHERE email IS NOT NULL
                              GROUP BY e HAVING COUNT(*) > 1)""")

