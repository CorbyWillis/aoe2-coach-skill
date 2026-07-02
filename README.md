# AoE2:DE Coach — an Age of Empires II skill for LLMs

An Age of Empires II: Definitive Edition coaching assistant, built as a
[Claude Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) but usable
with any LLM. Ask it things like:

> "I'm Persians in pocket on Black Forest, what's my best unit?"
>
> "How do I beat Goths as Britons?"
>
> "Best opening for Armenians on Arena?"

and get fast, accurate answers grounded in the **current** tech tree — not the model's
(often stale) training data.

## Why this design

LLMs know AoE2 fundamentals well, but balance patches constantly change tech trees, so
models confidently hallucinate outdated facts (e.g., Persians having Paladin). This
project splits knowledge into two layers:

1. **Generated facts** — compiled straight from the community-maintained
   [SiegeEngineers/aoe2techtree](https://github.com/SiegeEngineers/aoe2techtree) data
   (the same data behind [aoe2techtree.net](https://aoe2techtree.net)). One markdown
   file per civilization with bonuses, unique units/techs, the highest upgrade reachable
   on every unit line, and — most importantly — every generic tech the civ **cannot**
   research. Plus a full unit stats table with bonus damage in plain English.
2. **Hand-written strategy** — the things raw data can't tell you: counter
   relationships, map archetypes (Arabia, Arena, Black Forest, water), pocket/flank
   roles, and timing benchmarks.

The instructions (`SKILL.md`) force the model to read the relevant civ file before
making any tech-tree claim, which is what keeps a smaller/faster model like Claude
Sonnet accurate.

## Repository structure

```
aoe2-coach/
├── SKILL.md                    # Instructions for the LLM (Claude Skill format)
├── README.md                   # You are here
├── scripts/
│   └── update_data.py          # Regenerates all data files from aoe2techtree
└── references/
    ├── civ_index.md            # One-line summary of all 53 civs
    ├── civs/                   # One file per civ (generated)
    │   ├── persians.md
    │   ├── poles.md
    │   └── ... (53 files)
    ├── units.md                # Stats + bonus damage for every unit (generated)
    ├── counters.md             # Counter system (hand-written)
    └── strategy.md             # Maps, roles, timings (hand-written)
```

## Using with Claude (recommended)

**Claude.ai / Claude app:** package the folder as a `.skill` file (zip the directory,
or use the packaging flow in Claude's skill-creator) and upload it via Settings →
Capabilities → Skills. Ask any AoE2 question and the skill triggers automatically.

**Claude Code:** copy the folder to `~/.claude/skills/aoe2-coach/` (or
`.claude/skills/` inside a project). Done.

**Claude API:** attach the skill via the Skills feature, or simply include `SKILL.md`
in your system prompt and give the model file access to `references/` (e.g., in a
tool-use loop or code-execution container).

## Using outside Claude

Everything here is plain markdown, so it ports to any platform. The pattern is always
the same: *instructions + on-demand reference files*.

- **ChatGPT (custom GPT):** paste the body of `SKILL.md` into the GPT's instructions
  and upload `references/` files (civ files, `units.md`, `counters.md`, `strategy.md`)
  as Knowledge. File search retrieves the right civ file per question.
- **Any API (OpenAI, Gemini, local models via Ollama, etc.):**
  - *Small-context approach:* put `SKILL.md` + `counters.md` + `strategy.md` in the
    system prompt, and inject the relevant `references/civs/<civ>.md` file(s) once you
    detect the civ in the user's question (a simple keyword match against
    `civ_index.md` works fine). Total context stays under ~10K tokens.
  - *Big-context approach:* the entire `references/` folder is ~250 KB (~70K tokens);
    long-context models can just take all of it.
  - *RAG:* index `references/` in any vector store; the per-civ file layout chunks
    naturally.
- **Open WebUI / LM Studio / similar:** add the folder as a knowledge collection and
  set `SKILL.md` as the system prompt.

## Keeping the data current

After a patch or DLC, regenerate everything with one command (Python 3, no
dependencies):

```bash
python3 scripts/update_data.py
```

It downloads the latest `data.json` and English strings from aoe2techtree and rewrites
all files in `references/civs/`, `units.md`, and `civ_index.md`. Hand-written files
(`counters.md`, `strategy.md`) are never touched.

The script is intentionally strict: if a patch renames a unit, it fails with the exact
names that need fixing in the `LINES` table at the top of the script, rather than
silently producing wrong data. Regional replacement units (Winged Hussar replacing
Hussar for Poles/Lithuanians, Imperial Camel for Hindustanis, etc.) are modeled as
extra steps on their base line and annotated as replacements in the output.

## Credits

- Tech tree data: [SiegeEngineers/aoe2techtree](https://github.com/SiegeEngineers/aoe2techtree)
  (GPL-3.0), the project behind aoe2techtree.net.
- Age of Empires II: Definitive Edition © Microsoft Corporation. This is an unofficial
  fan project and is not affiliated with or endorsed by Microsoft.
