USE AWS EC2 or LOCAL MACHINE

MCP PLUGINS AND SKILLS


JEV LIVE RACE DEMO PASSCODE: (redacted, ask the team)

https://suki-pulse.vercel.app/
https://jev-live-race.vercel.app/ (passcode-gated)
https://jev-decision-race.vercel.app/

TRACK 03 OPTIONAL OPEN INNOVATION - HERMES x JEV



# Camp Run Hackathon Plan

Built from the slide photos in `assets/`, the starter repo, and read-only queries on the Suki Mart data. Event: Fri Oct 2, 2026, Avtica office, Makati.

## The QR codes, decoded

|Slide label|Link|What to do with it|
|-|-|-|
|Claim your API key (`20261002\_190546.jpg`, left)|https://hackathon-key-claim.vercel.app/|One key per person. Pick your team, enter your email. The page does not say which provider it is for; read the result page, then add it with `hermes model`. You already have a Claude token on this laptop, so treat the workshop key as a backup.|
|Hermes GitHub repository (same photo, middle)|https://github.com/pabilandokarenpv/Camp-Run-with-Hermes-Agent|The starter kit. Already cloned read-only to `C:\\Users\\eirmo\\camp\\Camp-Run-with-Hermes-Agent`. One teammate should fork it so the team can push.|
|Hermes setup guide|`docs/Hermes Setup Guide.pdf` (our own write-up)|CLI, Desktop, Telegram, local or VPS hosting, MCP servers, plus the WSL fixes we needed.|
|Submission form (`20261002\_191336.jpg`)|https://forms.gle/HMcvXVx2NC6392rH8 (Google Form)|Needs a Google sign-in, so the fields can't be read in advance. Have ready: team name, members, track, fork URL, a one-line problem statement, demo notes.|

## Rules that shape the plan

* Teams of 5. Build time is only **45 to 60 minutes**. Demo is **5 minutes**, live, from a laptop: problem, then how Hermes is used, then working output.
* Build **three connected layers** on the Suki Mart sandbox (`data/store.db`):

  1. **MCP server** (the hands): domain tools in `mcp-server/server.py`.
  2. **Skill** (the playbook): a `SKILL.md` that chains the tools.
  3. **Desktop plugin** (the face): a pane or Ctrl+K command in Hermes Desktop.
* Scoring, 100 points:

|Criterion|Points|What the judges look for|
|-|-:|-|
|MCP server|20|Domain-specific tools that run correctly. A generic `run\_sql` tool scores low.|
|Skill|20|A real multi-step chain that triggers from a natural prompt.|
|Desktop plugin|20|Works in Hermes Desktop and looks native.|
|End-to-end integration|10|GUI action, then skill, then MCP, then real data back in the GUI.|
|Relevance|15|Solves a real Business Operations or Customer Experience problem in the data.|
|Uniqueness|10|Not a copy of another team or an existing plugin.|
|Demo and pitch|5|Fits in 5 minutes with live proof.|

  Each 20-point layer: 0 not built, 1 to 7 started but not working, 8 to 14 works, 15 to 20 works well with thoughtful design. Ties go to Integration, then Relevance.

* Catalog MCPs (Neon, Supabase) and existing plugins do not count. AI-assisted coding is allowed.
* "Today" in the data is **2026-09-30 21:00**. Reset the data any time with `python data/seed.py`.

## Problems planted in the data (found with read-only queries)

Business Operations:

* **224** branch and product pairs are at or below their reorder point with **no open purchase order**.
* Ermita (ERM) has **14** items under 2 days of cover, all 14 at zero stock. Alabang (ALB), Katipunan (KAT) and Ortigas (ORT) have 15 each.
* Supplier promises are fiction: Visayas Canning promises 5 days and takes **11.3**, late **88%** of the time. Tropika Juice is late **85%** and short-ships **35%**.
* About **₱131k** of perishables at Alabang (ALB) expire within 3 days, and BGC and ORT are over ₱100k each.
* Promo `SEPT3X` was used on **211** orders with no budget and no discount recorded.
* Katipunan (KAT) and Kapitolyo (KPT) lose **7.1%** of shifts to no-shows and sick calls.

Customer Experience:

* **264** tickets are still open or pending, about **73 days old** on average. **46** never got a first response, 23 of them urgent.
* Worst-rated ticket categories: refunds (CSAT 3.03), promo codes, damaged items, loyalty points.
* About **300** one- and two-star reviews have no reply. Delivery is the top complaint (185).
* Tomas Morato (TMR) delivers **50%** late. One rider, Christian Lacson, has **63** late deliveries in the last 30 days.
* **142** loyalty accounts have a balance that does not match their points ledger. About 29,000 points expire within 30 days across 418 active accounts.
* **147** opted-in regulars (3+ orders) have not ordered in 60 days. The customer list has **46** duplicate emails.

## Idea options

**A. Suki Recovery Desk (Customer Experience). Recommended.**
One customer often hits several planted problems in a row: a late delivery, then a ticket nobody answered, then a one-star review with no reply, and loyalty points that are wrong. The desk finds those customers, shows each one's full story in one place, and fixes it: corrects the points, replies to the review, and resolves the ticket. It ties four tables together, which is hard to copy and scores well on relevance.

**B. Restock Radar (Business Operations).** A morning brief: stockout risks, no open PO, real supplier lead times, expiring stock to move between branches, then draft the purchase orders. Strong data, but the starter README uses `find\_stockout\_risks` as its example, so several teams will likely build this, which costs uniqueness points.

**C. Delivery Control Tower (both tracks).** Late deliveries by branch and rider, linked to the tickets and reviews they caused, with a coaching or reassignment action. Original, but the action side is thinner.

## Build plan for A (Suki Recovery Desk)

### Layer 1: MCP tools (`mcp-server/server.py`, server name `suki`)

|Tool|Type|What it answers|
|-|-|-|
|`find\_at\_risk\_customers(branch\_code=None, days=30, limit=10)`|read|Customers with an open ticket, an unreplied 1 or 2 star review, or a late or failed delivery in the window, ranked by a simple score.|
|`get\_customer\_story(customer\_id)`|read|Timeline of recent orders, deliveries (late or not), tickets, reviews, loyalty tier, and points expiring.|
|`check\_loyalty\_balance(customer\_id)`|read|Stored balance against the ledger sum, and the difference.|
|`credit\_loyalty\_points(customer\_id, points, reason)`|write|Inserts an `adjust` transaction and updates the balance.|
|`reply\_to\_review(review\_id, reply\_text)`|write|Sets `replied\_at` and `reply\_text`.|
|`resolve\_ticket(ticket\_id, resolution\_note)`|write|Sets the status to resolved and stamps `first\_response\_at` if it is empty.|
|`branch\_recovery\_scorecard(branch\_code)`|read|Open tickets, unreplied low reviews, late delivery %, ledger mismatches for one branch.|

Keep SQL inside each tool, return about 20 rows at most, and write each docstring for the AI.

### Layer 2: skill (`skills/suki-recovery-desk/SKILL.md`, `name: suki-recovery-desk`)

1. Trigger on phrases like "who should we recover today", "at-risk customers at BGC", "fix this customer".
2. Call `find\_at\_risk\_customers`, then `get\_customer\_story` for the top one.
3. Decide using rules: a points mismatch gets a correction; a late delivery gets a goodwill credit (for example 100 points); an unreplied review gets a short, warm reply that names the fix.
4. Show the plan, ask for confirmation, then call the write tools.
5. Output: a one-line headline, a table (customer, problems, action taken), and the review reply text.

### Layer 3: desktop plugin (`desktop-plugin/suki-recovery-desk/plugin.js`, `id: 'suki-recovery-desk'`)

* A right-side pane with a branch picker and three buttons: "At-risk customers", "Recover top customer", "Branch scorecard". Each button sends a prompt that names the skill.
* A Ctrl+K command: "Suki: Recover top customer".
* Use only `jsx()` and `jsxs()`, theme variables, and the three allowed imports.

### Team split (60 minutes)

|Person|0 to 15 min|15 to 30 min|30 to 50 min|50 to 60 min|
|-|-|-|-|-|
|1|Read tools|Fix tool bugs from tests|Help integrate|Demo driver|
|2|Write tools|`hermes mcp test suki`|Help integrate|Backup laptop|
|3|Draft the skill against the tool names|Install and trigger the skill|Tune the trigger wording|Rehearse|
|4|Plugin scaffold from the template|Wire buttons to skill prompts|Polish the pane|Rehearse|
|5|Pick 2 demo customers from the data|Write the 5-minute script|Fill the submission form, fork, push|Timekeeper|

### 5-minute demo

1. Problem (45 s): "This customer's delivery was late, her ticket is 70 days old, her one-star review has no reply, and her points are wrong."
2. Click "At-risk customers" in the pane. The skill runs, and the MCP tools return the list.
3. Click "Recover top customer". Show the story, confirm, and watch the fixes land.
4. Click "Branch scorecard" again and point to the numbers that dropped.
5. Close: three layers connected, real data changed, and it works for any branch.

## Setup on this laptop (Windows, native Hermes)

* Repo: `C:\\Users\\eirmo\\camp\\Camp-Run-with-Hermes-Agent`. It stays outside `C:\\dev` because the MCP server writes to `store.db`, and a live database should not sync to riePC.
* `uv` comes with Hermes at `%LOCALAPPDATA%\\hermes\\tools\\uv-0.12.3-win32-x64\\uv.exe`. If `uv --version` fails in a new terminal, use that full path.
* Register the server once Hermes is installed, then restart Hermes:

```powershell
  hermes mcp add suki --command uv --args run C:\\Users\\eirmo\\camp\\Camp-Run-with-Hermes-Agent\\mcp-server\\server.py
  hermes mcp test suki
  ```

* **Watch the paths.** The README's Windows paths use `%USERPROFILE%\\.hermes`, but native Windows Hermes lives in `%LOCALAPPDATA%\\hermes`. Check with `hermes config path`, then copy skills to `%LOCALAPPDATA%\\hermes\\skills\\<name>` and plugins to `%LOCALAPPDATA%\\hermes\\desktop-plugins\\<name>`.
* Skills load in new chats only. MCP changes need a Hermes restart. Plugins reload with Ctrl+K, "Reload desktop plugins".

