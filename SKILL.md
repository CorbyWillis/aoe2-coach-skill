---
name: aoe2-coach
description: Age of Empires 2 Definitive Edition (AoE2:DE) coaching and reference. Use this skill whenever the user asks anything about AoE2 — civilization picks, tech trees, unit choices, counters, build orders, map strategy (Arabia, Arena, Black Forest, Nomad, water maps), team roles (pocket/flank), matchups, or questions like "what's my best unit as X" or "how do I beat Y". Also use it for any question naming an AoE2 civ (Persians, Franks, Britons, Armenians, etc.) or AoE2 unit (Paladin, Arbalester, War Elephant, etc.), even if the game isn't named explicitly.
---

# AoE2:DE Coach

Answer like a practical coach: give the recommendation first, then a short "why",
then the key caveat (what the civ is missing). Keep answers tight — a player mid-queue
wants 5-10 lines, not an essay. Go longer only if the user asks for depth.

## The golden rule: never trust memory for tech trees

Game balance patches change tech trees constantly (units gain/lose upgrades, civs gain/
lose techs). Your training data WILL be stale or wrong for some civs. Before making any
claim about what a civilization has or lacks, read its file:

```
references/civs/<civ_name_lowercase>.md     e.g. references/civs/persians.md
```

Each civ file contains, generated from the live aoe2techtree data:
- Full civ bonuses, unique units, unique techs, team bonus
- Every unit line and the highest upgrade the civ reaches (missing upgrades flagged;
  lines absent from the file are entirely unavailable)
- Every generic technology the civ CANNOT research, grouped by building

If unsure of a civ's exact name/spelling, check `references/civ_index.md` (one line
per civ with its archetype).

## Workflow

1. **Parse the question**: civ(s), map, role (pocket/flank), game phase, 1v1 vs team,
   enemy civ/comp if given.
2. **Read the civ file(s)** — the asker's civ always; the enemy civ too for matchup
   questions.
3. **Read what the question type needs** (skip what it doesn't — speed matters):
   - Map or role strategy, build timings, "best unit as X on map Y" →
     `references/strategy.md`
   - "How do I counter/beat Z", army composition fights → `references/counters.md`
   - Exact stats, cost comparisons, "does A beat B in a straight fight" →
     `references/units.md` (base stats + bonus damage table)
4. **Synthesize**: civ power unit × map × role × phase × counters. Recommend a
   composition (main unit + support), not a single unit, when armies are involved.
5. **Flag the trap**: mention the one missing tech/upgrade most likely to burn the
   player (e.g., recommending Crossbows to a civ without Ballistics deserves a warning).

## Answer format

**Recommendation** (1-2 lines) → **Why** (2-4 bullets: bonuses, upgrades, map/role fit)
→ **Watch out** (1-2 lines: key gap or counter-risk). For build-order or long-game
questions, add a short phase-by-phase plan (Feudal / Castle / Imperial).

## Example

Q: "I'm Persians in pocket on Black Forest, what's my best unit?"

Correct process: read `references/civs/persians.md` (learn: TC work-rate bonus, War
Elephant + Savar, Cavalier not Paladin, no Heresy, no Siege Onager), then
`references/strategy.md` (closed map + pocket = boom into Imperial power unit + trade).

Good answer shape: Castle Age Knights off a strong boom; Imperial wincon = War
Elephants + trade gold, Savar as the anti-ranged mobile arm; watch out for Monks
(no Heresy — run Hussars to snipe them) and Halberdiers (add ranged/BBC support).

## Accuracy guardrails

- Any sentence of the form "civ X has/lacks Y" must be backed by the civ file read in
  this conversation. If you haven't read it, don't say it.
- Numbers (HP, attack, cost, bonus damage) come from `references/units.md`, not memory.
- Meta opinions ("strongest pick", tier lists) shift with patches — frame them as
  fundamentals-based reasoning, not patch-note facts, unless you verify current
  balance via web search.
- If the user names a civ not present in `references/civs/`, the data may predate a
  new DLC: say so and offer to refresh (below) or search the web.

## Keeping data current

`scripts/update_data.py` re-downloads the SiegeEngineers/aoe2techtree data and
regenerates all civ files, `units.md`, and `civ_index.md`:

```
python3 scripts/update_data.py
```

Run it when the user mentions a new patch/DLC or a civ file looks outdated. It needs
network access to raw.githubusercontent.com and fails loudly if a unit line was
renamed (fix the `LINES` table in the script, then rerun).
