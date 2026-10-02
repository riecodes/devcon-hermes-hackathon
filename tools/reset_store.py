"""Reset the Suki Mart store.db while other processes keep it open.

seed.py deletes and recreates the file, which Windows refuses while the suki MCP servers
hold it. So: build a fresh database with seed.py into a temp file, then copy it INTO the
live file with SQLite's online backup (a page-level copy that also drops tables the fresh
build doesn't have, like jev_triage and pulse_actions).
"""
import importlib.util
import os
import sqlite3
import tempfile

DATA = r"C:\dev\devcon\hermes-hackathon\Camp-Run-with-Hermes-Agent\data"
spec = importlib.util.spec_from_file_location("seed", os.path.join(DATA, "seed.py"))
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)

fresh = os.path.join(tempfile.gettempdir(), "suki-fresh-store.db")
seed.DB_PATH = fresh  # main() reads the module global at call time
seed.main()

src, dst = sqlite3.connect(fresh), sqlite3.connect(os.path.join(DATA, "store.db"), timeout=30)
src.backup(dst)
dst.close()
src.close()
os.remove(fresh)

c = sqlite3.connect(f"file:{os.path.join(DATA, 'store.db')}?mode=ro", uri=True)
one = lambda sql: c.execute(sql).fetchone()[0]  # noqa: E731
print("extra tables left:", [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE name IN ('jev_triage','pulse_actions')")])
print("all open tickets:", one("SELECT COUNT(*) FROM support_tickets WHERE status IN ('open','pending')"))
print("TMR open tickets:", one("SELECT COUNT(*) FROM support_tickets t JOIN branches b ON b.id = t.branch_id "
                               "WHERE b.code = 'TMR' AND t.status IN ('open','pending')"))
print("loyalty mismatches:", one("SELECT COUNT(*) FROM loyalty_accounts a WHERE a.points_balance != "
                                 "(SELECT COALESCE(SUM(points), 0) FROM loyalty_transactions t WHERE t.loyalty_account_id = a.id)"))
