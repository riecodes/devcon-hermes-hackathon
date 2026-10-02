"""Jev Live Race: local web app. Jev and Claude Haiku 4.5 answer the same complaint, live.

Run:   python app.py        then open http://127.0.0.1:8790
Keys are read from disk by bench.read_keys() and never leave this process.
Binds to 127.0.0.1 only. (Port 8787 is taken by another project's wrangler dev.)
"""
import json
import os
import random
import re
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from bench import (CAUSES, JEV_MODEL, JEV_URL, LLM_MODEL, LLM_SYSTEM, PRICE, ZEN_URL,
                   jev_questions, load_items, post, read_keys, state_of)

HERE = os.path.dirname(os.path.abspath(__file__))
ADDR, PORT = "127.0.0.1", 8790
JEV_KEY, ZEN_KEY = read_keys()
ITEMS = load_items(200)
BATCH_LOCK = threading.Lock()


def jev(text: str, q: int = 8) -> dict:
    qs = jev_questions(n_extra=max(0, q - 8), only=q if q < 8 else None)
    data, ms = post(JEV_URL, {"Authorization": f"Bearer {JEV_KEY}"},
                    {"model": JEV_MODEL, "state": state_of({"src": "message", "id": 0, "text": text}), "questions": qs})
    a = data["answers"]
    causes = {c: round(float(a[c]["noul"]), 3) for c in CAUSES if c in a}
    tin = int(data.get("usage", {}).get("input_tokens", 0))
    return {"ms": round(ms, 1), "tokens_in": tin, "tokens_out": 0, "cost_usd": round(tin * PRICE["jev_in"] / 1e6, 8),
            "causes": causes, "churn_risk": float(a["churn_risk"]["score"]) if "churn_risk" in a else None,
            "urgent": float(a["urgent"]["noul"]) if "urgent" in a else None,
            "top": max(causes, key=causes.get) if causes else None}


def llm(text: str) -> dict:
    data, ms = post(ZEN_URL, {"x-api-key": ZEN_KEY, "anthropic-version": "2023-06-01"},
                    {"model": LLM_MODEL, "max_tokens": 200, "system": LLM_SYSTEM,
                     "messages": [{"role": "user", "content": state_of({"src": "message", "id": 0, "text": text})}]})
    raw = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    m = re.search(r"\{.*\}", raw, re.S)
    parsed = json.loads(m.group(0)) if m else {}
    causes = {c: round(float(parsed.get(c, 0) or 0), 3) for c in CAUSES}
    u = data.get("usage", {})
    tin, tout = int(u.get("input_tokens", 0)), int(u.get("output_tokens", 0))
    return {"ms": round(ms, 1), "tokens_in": tin, "tokens_out": tout,
            "cost_usd": round((tin * PRICE["llm_in"] + tout * PRICE["llm_out"]) / 1e6, 8), "causes": causes,
            "churn_risk": float(parsed.get("churn_risk", 0) or 0), "urgent": float(parsed.get("urgent", 0) or 0),
            "top": max(causes, key=causes.get) if any(causes.values()) else None}


def once_retry(fn, *args):
    try:
        return fn(*args)
    except Exception:  # one retry for a flaky network call, then report the error
        time.sleep(0.8)
        return fn(*args)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet: no per-request stderr writes
        pass

    # ---------- plumbing ----------
    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, name: str) -> None:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            return self._json(404, {"error": f"{name} not found"})
        body = open(path, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sse_open(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        lock = threading.Lock()

        def send(event: str, data: dict) -> None:
            with lock:
                try:
                    self.wfile.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
        return send

    def _text(self, q) -> str | None:
        text = (q.get("text", [""])[0] or "").strip()[:1200]
        return text or None

    # ---------- routes ----------
    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        q = urllib.parse.parse_qs(url.query)
        route = {"/": lambda: self._file("live.html"), "/recorded": lambda: self._file("index.html"),
                 "/api/sample": lambda: self.sample(q), "/api/race": lambda: self.race(q),
                 "/api/batch": lambda: self.batch(q), "/api/scale": lambda: self.scale(q)}.get(url.path)
        if route is None:
            return self._json(404, {"error": "not found"})
        route()

    def sample(self, q):
        n = max(1, min(40, int((q.get("n") or ["1"])[0] or 1)))
        self._json(200, [{k: it[k] for k in ("id", "src", "branch", "text")} for it in random.sample(ITEMS, n)])

    def race(self, q):
        text = self._text(q)
        if not text:
            return self._json(400, {"error": "Type or pick a complaint first."})
        qn = max(1, min(16, int((q.get("questions") or ["8"])[0] or 8)))
        send = self._sse_open()
        t0 = time.perf_counter()
        send("start", {"t0": 0})

        def run(model, fn, *args):
            try:
                r = once_retry(fn, *args)
                send("result", {"model": model, "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1), **r})
            except Exception as exc:
                send("result", {"model": model, "error": f"{type(exc).__name__}: {str(exc)[:120]}"})

        threads = [threading.Thread(target=run, args=("jev", jev, text, qn)), threading.Thread(target=run, args=("llm", llm, text))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        send("done", {})

    def batch(self, q):
        if not BATCH_LOCK.acquire(blocking=False):
            return self._json(429, {"error": "A batch race is already running"})
        try:
            n = max(5, min(40, int((q.get("n") or ["20"])[0] or 20)))
            c = max(1, min(8, int((q.get("concurrency") or ["8"])[0] or 8)))
            picks = random.sample(ITEMS, n)
            send = self._sse_open()
            t0 = time.perf_counter()
            send("start", {"n": n, "concurrency": c})

            def lane(model, fn):
                cost, ok = 0.0, 0

                def one(i_it):
                    nonlocal cost, ok
                    i, it = i_it
                    try:
                        r = once_retry(fn, it["text"])
                        cost += r["cost_usd"]
                        ok += 1
                        send("tick", {"model": model, "i": i, "ms": r["ms"], "top": r["top"], "ok": True,
                                      "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1)})
                    except Exception:
                        send("tick", {"model": model, "i": i, "ok": False, "top": None,
                                      "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1)})

                with ThreadPoolExecutor(max_workers=c) as pool:
                    list(pool.map(one, enumerate(picks)))
                wall = (time.perf_counter() - t0) * 1000
                send("summary", {"model": model, "wall_ms": round(wall, 1), "per_sec": round(n / (wall / 1000), 2),
                                 "cost_usd": round(cost, 6), "ok": ok})

            lanes = [threading.Thread(target=lane, args=("jev", jev)), threading.Thread(target=lane, args=("llm", llm))]
            for t in lanes:
                t.start()
            for t in lanes:
                t.join()
            send("done", {})
        finally:
            BATCH_LOCK.release()

    def scale(self, q):
        text = self._text(q)
        if not text:
            return self._json(400, {"error": "Type or pick a complaint first."})
        k = max(1, min(16, int((q.get("questions") or ["8"])[0] or 8)))
        try:
            r = once_retry(jev, text, k)
            self._json(200, {"questions": k, "ms": r["ms"], "tokens_in": r["tokens_in"], "cost_usd": r["cost_usd"]})
        except Exception as exc:
            self._json(502, {"error": f"Jev call failed: {type(exc).__name__}"})


if __name__ == "__main__":
    server = ThreadingHTTPServer((ADDR, PORT), Handler)
    server.daemon_threads = True
    print(f"Jev Live Race on http://{ADDR}:{PORT}", flush=True)
    server.serve_forever()
