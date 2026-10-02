# Motion studio rules

This film is built with the motion-design skill (`~/.claude/skills/motion-design`). Read its SKILL.md before a big change.

## Render contract
- The film is a pure function of time: `window.seek(t)` in `index.html` paints frame t.
- No CSS transitions, no setTimeout, no requestAnimationFrame in render mode, no state carried between frames. Seeded noise only (`rng(seed)`), never `Math.random`.
- Motion is springs (`spring`, `track`), never fixed easing curves. Tiny overshoot on UI, none on type.
- Scenes are laid out from `W`, `H` and `U` (1% of the short side), never fixed pixels, so every format renders from one timeline.
- Render with the skill's `scripts/render.mjs`. H.264, yuv420p, CRF 16.

## Look
- Banned: centered title on a gradient, everything fading in, corner labels and frame borders, glow on UI chrome, generic particle bursts.
- One display face, one UI face. One accent color unless the brief says otherwise.
- Something new happens on screen every 2 to 4 seconds.
- Real product UI, logos and numbers only (from `assets/`). Never invent screens or stats.

## Sound
- Use the supplied track, or synthesize the score in code. SFX come from the skill's `scripts/sfx.mjs`.
- Hits sit on the beat grid (`beats.js`). Master to -14 LUFS.

## Loop before you show me anything
1. Render a contact sheet (one frame per beat) and look at it.
2. Score 1-10: hook in the first 2 s, readability at phone size, motion quality, variety, composition, brand accuracy, sound sync.
3. Fix the 3 worst problems. Repeat until every score is 8+.
4. Only then do the full render.
