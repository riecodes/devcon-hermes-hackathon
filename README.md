# Suki Pulse · Camp Run Hermes Agent Hackathon

Everything we built for **CAMP / RUN: Build Overnight with Hermes Agent** (DEVCON Manila × Avtica × Amihan, Avtica office, Makati, October 2, 2026).

**Suki Pulse** turns Suki Mart's customer complaints into operational fixes, in one click inside Hermes Desktop. Hermes runs the loop: TypeSafe Jev labels every complaint in about half a second, our MCP tools trace each cause into operations (riders, stock, suppliers, the loyalty ledger), and Hermes fixes both sides after asking first. Track: Open Innovation (Business Operations + Customer Experience).

## Live links

| What | Link |
|---|---|
| Suki Pulse dashboard (full Jev run, 694 complaints, 12 branches) | https://suki-pulse.vercel.app/ |
| Jev Live Race (retired after the event: API keys removed, page still loads) | https://suki-pulse.vercel.app/race/ |
| Jev Decision Race (recorded benchmark) | https://suki-pulse.vercel.app/benchmark/ |
| Code (fork of the starter kit) | https://github.com/riecodes/Camp-Run-with-Hermes-Agent |
| Pitch deck (private Claude artifact) | https://claude.ai/artifact/9zHdDFmBhLroG2ooyebfuJ |
| Laptop prep checklist (private Claude artifact) | https://claude.ai/artifact/YQGkM314b2dPfGz8PeRpd2 |

One site, one domain. The old jev-live-race.vercel.app and jev-decision-race.vercel.app now only redirect there (`redirects/`).

## What's in this folder

| Folder | What it is | Made by |
|---|---|---|
| `Camp-Run-with-Hermes-Agent/` | The three layers: `mcp-server/server.py` (10 `suki` tools), `skills/suki-pulse/`, `desktop-plugin/suki-pulse/`, on the Suki Mart sandbox (`data/store.db`, 221,142 rows). A git submodule: our fork of the organizers' starter kit. | Hermes |
| `suki-pulse-site/` | The one deployed site (suki-pulse.vercel.app): `/` the dashboard of the full Jev run (Hermes), `/race/` the live race page + `api/` functions with guardrails (passcode, same-origin, per-visitor limits, 600-char text, batches of 20), `/benchmark/` the recorded race | Hermes, Claude Code |
| `redirects/` | Redirect-only Vercel projects for the two old domains | Claude Code |
| `jev-speed/` | `bench.py` (Jev vs Claude Haiku 4.5 benchmark), `data.json` (measured results), `build.py` + `template.html` (recorded page), `app.py` + `live.html` (local live race on 127.0.0.1:8790), `build_live_deploy.py` | Claude Code |
| `videos/` | Demo films: `remotion/` (final cut `out/suki-pulse-draft-a-sound.mp4`), `film/`, `shots/` | Claude Code (video session) |
| `pitch/` | `script/` (pitch scripts and notes), `deck/` (source files of the Claude Slides deck), `qr/` (QR codes + `make_qr.py`, each verified to decode) | Claude Code |
| `docs/` | `PLAN.md` (idea, QR decodes, data findings, build plan), our Hermes setup guide (`Hermes Setup Guide.pdf`), the prep checklist page, Suki Pulse write-ups | Claude Code, Hermes |
| `tools/` | `probe_suki.py` (planted problems), `pitch_facts.py` (every pitch number), `reset_store.py` (reset the data while Hermes holds it open), `verify_pulse.py`, `promo_check.py`, `decode_qr.py` | Claude Code |
| `assets/` | Photos of the event slides (challenge, QR codes, judging) | us |

## Run it

```powershell
# Hermes: register the MCP server (absolute path; restart Hermes Desktop after)
hermes mcp add suki --command uv --args run C:\dev\devcon\hermes-hackathon\Camp-Run-with-Hermes-Agent\mcp-server\server.py

# Reset the Suki Mart data (works even while Hermes has it open)
python tools\reset_store.py

# Local live race (Jev vs Haiku), then open http://127.0.0.1:8790
cd jev-speed; python app.py

# Re-measure and rebuild the recorded page
cd jev-speed; python bench.py; python bench.py --haiku-burst; python build.py

# Rebuild the live race page into the site, then deploy the one site
cd jev-speed; python build_live_deploy.py
cd ..\suki-pulse-site; vercel deploy --prod
```

## Secrets

No key is stored in this folder. The TypeSafe key lives in `C:\dev\.secrets\devcon-typesafe-jev.key`, the OpenCode Zen key in Hermes's own `.env` (`%LOCALAPPDATA%\hermes\.env`), and the deployed live race read `TYPESAFE_API_KEY`, `OPENCODE_ZEN_API_KEY` and `DEMO_PASSCODE` from encrypted environment variables on the `suki-pulse` Vercel project. All three were removed on October 3, 2026, so the paid routes now refuse every request; set them again and redeploy to bring the race back. `data/store.db` is Syncthing-ignored because the MCP server writes to it live.

## Measured numbers (October 2, 2026)

- Jev median 586 ms vs Claude Haiku 4.5 2.29 s on the same 40 complaints and 8 questions (3.9x faster); $0.000023 vs $0.000829 per decision (35x cheaper).
- All 694 open complaints across 12 branches: 64.7 s, 388,465 input tokens, $0.0163, zero fallbacks.
- Suki Mart is fictional sandbox data from the organizers' starter kit.
