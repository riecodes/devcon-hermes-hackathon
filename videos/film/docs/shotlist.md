# Suki Pulse film: story beats (design on hold)

Grid: 120 BPM, beat k = k x 0.5 s, 20 s = 40 beats = 10 bars. 1920x1080 first, then 1080x1920 from the same timeline.
Every value on screen is read from `window.SUKI` (`D` in index.html). Rows marked PLACEHOLDER read `D.fix_run`, which stays a projection until the live fix run, then `python videos/make_data.py` swaps in the real rows with no code edit.
This file fixes story, order, timing and data only. Look, type, color, camera and transitions wait for the new design.

| # | Beats | Time (s) | On screen (data source) | Text | SFX cue type |
|-|-|-|-|-|-|
| 1 | 0-4 | 0.0-2.0 | Hook: one real complaint, `D.complaints[0]` (TKT-00585, high priority ticket) | the quote, plus its ref | thump 0.0, pop on the quote |
| 2 | 4-8 | 2.0-4.0 | More real complaints arrive one per beat, `D.complaints[1..4]`; then the total, `D.jev_run.items` open complaints across `D.jev_run.branches` branches | "694 open complaints. 12 branches." then the first sentence of `D.pitch` ("Every complaint at Suki Mart is a symptom.") | pop per complaint |
| 3 | 8-14 | 4.0-7.0 | Jev reads one real sample, `D.branch.jev_samples[1]` (review #270): the six yes/no checks from `D.cause_labels`, only the real hit (`causes`) answers yes, then churn `churn`/2 | "TypeSafe Jev: one call, six yes/no root-cause checks" (from `D.layers[3].body`) | click per check, pop on the churn score |
| 4 | 14-18 | 7.0-9.0 | The whole chain at once, `D.jev_run`: items, seconds, cost_usd, fallbacks, engine | 694 complaints, 64.7 s, $0.0163, 0 fallbacks, jev-1.13.0 | thump on beat 16 |
| 5 | 18-24 | 9.0-12.0 | Root causes by branch from `D.heatmap` (crop the real dashboard screenshot once the redesign ships), then Tomas Morato singled out with `D.branch.causes` | "Late delivery explains 16 of 37 complaints at Tomas Morato." (`D.branch.causes.late_delivery`, `D.branch.items`, `D.branch.name`) | whoosh 2 frames before beat 18, pop on the TMR highlight |
| 6 | 24-28 | 12.0-14.0 | The operational proof, `D.branch.rider` | "Christian Lacson: 63 late of 85 deliveries across 10 branches." plus the fix tool `flag_rider_for_coaching` | thump on beat 24 |
| 7 | 28-34 | 14.0-17.0 | Fix both sides: `D.fix_run.prompt`, the confirm step "Proceed? (yes/no)" then "yes" (SKILL.md workflow B copy), then `D.fix_run.actions` ticking one per beat, as tool, target, result (PLACEHOLDER) | tool names and targets | click per action |
| 8 | 34-37 | 17.0-18.5 | Before and after, `D.branch.scorecard_before` against `D.fix_run.scorecard_after`, only the rows that changed (PLACEHOLDER) | open tickets, never answered, unreplied 1-2 star reviews, loyalty mismatches, low stock with no PO | pop per row |
| 9 | 37-40 | 18.5-20.0 | End card: `D.product` wordmark, `D.tagline`, the three layers plus TypeSafe Jev from `D.layers`, `D.credits`, `D.url` | as data | thump on beat 37 |

Open data gaps (decide before styling):
- Beat 6 wants "in 30 days": the 30-day window lives in server.py (`root_cause_rollup`), not in SUKI. Add `"days": 30` to `branch.rider` in make_data.py rather than hardcoding it here.
- Beat 7 shows a review reply only if the redesign keeps one: `D.fix_run.reply` is a PLACEHOLDER too.
