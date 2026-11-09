# KuKu Promo Finder — System Overview

**What this product does**  
Given episode scripts for an audio / micro-drama, it finds short **storytelling windows** that can work as **promos**, scores them, builds a **per-episode catalogue** and a **campaign Priority pack**, then surfaces both in a web app for human review.

This document is written from **first principles**, mapped to a **real studio**, then grounded in **what the code actually does** (verified against `src/` + `web/`, not only experiment reports).

For the head-to-head of rule / hybrid / llm on episodes 1–50:

**→ [Mode Comparison Report](../output/full_compare/MODE_REPORT.md)**

---

## 0. Code-verified truth table (read this first)

| Claim | Verified in code? | Exact behavior |
|-------|-------------------|----------------|
| Promos are story windows, not single lines | **Yes** | `candidate_generator.expand_window` builds multi-beat ranges |
| Target duration ~20–60s | **Mostly** | Docs/comments say ~15–60s; expansion uses max windows up to 40–90s internally; marketer accepts **14–62s** |
| Mini-arc = open → build → cliff | **Yes (rule heuristics)** | `mini_arc_validator._rule_based_validation` |
| Mini-arc LLM path used in product runs | **No (today)** | `run_targeted_pipeline` always calls validate with `llm_client=None` → rule path only (LLM/hybrid mini-arc code exists but is not wired with a client) |
| Window expansion is mode-dependent | **No** | Always `generate_story_windows(..., mode="rule")` |
| Scoring modes rule / hybrid / llm | **Yes** | `run_scoring_and_classification` |
| Hybrid changes numeric scores via LLM | **No** | Hybrid = **rule scores** + LLM polish of **hook_type / reason / promo_types** on top-N per episode only |
| LLM mode re-scores numbers | **Yes (top-N/ep)** | Rule baseline all → LLM `score_candidate` on top `llm_per_episode` (default **5**) per episode |
| No API key → rule fallback | **Yes** | Orchestrator + scorer force `effective_mode = "rule"` if no `GROQ_API_KEY` / client |
| Types kill weak promos | **No** | Types are tags; **not** in `compute_global_score`; soft type-repeat penalty only inside diversity packing |
| Two outputs: By episode + Priority | **Yes** | Per-ep Top‑K harvest + `build_campaign_pack` on **full finals pool** |
| Campaign pack = only 1 champ/ep | **No** | Pack is built from **full harvest finals**; champions are a separate catalogue layer |
| Series ranker formula | **Yes** | Weighted blend (below) |
| Marketer protect / reject | **Yes** | Rule marketer; web sets `marketer_use_llm=False` |
| Generate writes real pipeline artifacts | **Yes** | `run_targeted_pipeline` → harvest JSON → `write_deliverable` |
| Page load re-runs pipeline | **No** | UI loads last saved project / mode results |
| “Load demo results” = live pipeline | **No** | Loads precomputed compare/final artifacts for review |

---

## 1. First principles (why the system is shaped this way)

### The naive approach fails

Scanning for “spicy lines” and cutting 15 seconds around them produces **clips**, not **promos**.

A promo has a job:

| Job | Meaning |
|-----|---------|
| **Stop the scroll** | Strong open in the first seconds |
| **Tell a tiny story** | Not a random middle — a complete mini beat |
| **Leave an open loop** | End on tension / unfinished emotion (cliff) |
| **Stand alone enough** | Cold viewer still *feels* something |
| **Serve the series** | Early acquire; late don’t over-spoil |

So the system is built around **story windows with a mini-arc**, not line snippets.

### Principle 1 — A promo is a mini-story

```
HOOK  →  BUILD / TURN  →  CLIFF
(open)     (pressure)      (unresolved)
```

### Principle 2 — Two questions → two lists

| Question | Output | Code path |
|----------|--------|-----------|
| Best promos **inside** episode N? | **By episode** Top‑K | `rank_and_select` per episode |
| What should we **post first** across the show? | **Priority / campaign pack** | `build_campaign_pack` + marketer on full finals |

### Principle 3 — Labels are tags, not gates

`promo_types` help browsing and **soft** diversity in packing.  
They are **excluded** from the global score formula. A strong “soft” emotional beat can still rank and ship.

### Principle 4 — Machines propose; humans (and a marketer pass) dispose

Automation:

1. Covers every episode systematically  
2. Proposes a large honest pool  
3. Ranks with series context  
4. Applies a conservative marketer trim  

Humans still own final taste. This is a **decision accelerator**.

### Principle 5 — Prefer a mode that works when the API is down

**Hybrid** is the product default: rule core + optional LLM polish + automatic rule fallback.

---

## 2. Studio analogy — real workflow vs our system

| Real studio role | What they do | Our counterpart (code) |
|------------------|--------------|-------------------------|
| **Editor / trailer cutter** | Watches every ep, marks promo-worthy spans, cuts duration | `parser` → `candidate_generator` → `mini_arc_validator` → local scores |
| **Series producer** | Knows spine, people, themes | `series_continuity_map` |
| **Growth / social lead** | Picks feed order from a big pile | `series_ranker.compute_global_score` + `diversity_pack` |
| **Marketer / brand lead** | Kills weak / risky / redundant; protects stars | `marketer_agent` |
| **Review board** | Final look + export | Web UI (Priority, By episode, Continuity) |

### Side-by-side

```
STUDIO                                    THIS SYSTEM (actual)
──────                                    ────────────────────
Editor watches every ep          →        Parse scripts + expand story windows (always rule)
Marks “this could be a promo”    →        Mini-arc validate (rule in live runs) + score + type
Episode shortlist                →        rank_and_select Top-K / ep  →  By episode UI
Shared drive of all candidates   →        Harvest finals JSON (full pool)
Growth ranks what to post        →        Continuity map + series_global_score + diversity pack
Marketer kills / protects        →        marketer_trim_pack → Campaign / Priority
Team reviews                     →        Web app + CSV/JSON export
```

---

## 3. Technical pipeline (as implemented)

### Entry points

| Entry | What runs |
|-------|-----------|
| **Web Generate** (project) | Link scripts → parse → `run_targeted_pipeline` → write harvest → `write_deliverable` → load into project UI |
| **CLI / scripts** | Same core modules (`orchestrator`, `final_deliverable`) |
| **Load demo results** | Read precomputed `output/full_compare` + `output/final` packs (not a live re-score) |

### Step-by-step (code order)

```
① PARSE
   parser / scan_folder(parse=True)
   → episodes with scenes, beats, dialogue, timestamps, loglines

② STORY WINDOW EXPANSION          [always rule]
   candidate_generator.generate_story_windows(episodes, mode="rule")
   → many candidate ranges (~15–60s storytelling windows; internal expand caps 40–90s)

③ MINI-ARC VALIDATION             [rule in live orchestrator]
   mini_arc_validator.validate_candidates(..., llm_client=None)
   → keep windows that look like hook→escalation→cliff
   → if zero valid: fall back to raw windows (orchestrator safety)

④ SCORE + TYPE                    [rule | hybrid | llm]
   llm_agents.run_scoring_and_classification(mode=effective_mode)
   → always rule-score everyone first
   → hybrid: LLM refines top-N/ep (types + rationale only)
   → llm:    LLM re-scores top-N/ep (numeric scores)
   → no client / no GROQ_API_KEY → force rule

⑤ PER-EPISODE TOP-K
   orchestrator.rank_and_select
   → hard filter: hook & cliff ≥ 3.5 (0–10)
   → diversity: prefer spacing (min_gap_sec = 4.0)
   → keep top_k (web default often 5)
   → this harvest = “finals” pool + By episode catalogue

⑥ SERIES CONTINUITY MAP
   series_continuity_map (from processed episode data)
   → characters, themes, arc phases, spoiler guidance, one-liner

⑦ SERIES RANK + DIVERSITY PACK    [on FULL finals, not only 1/ep]
   series_ranker.compute_global_score + build_campaign_pack
   → series_global_score for every final
   → diversity_pack (default max 2 per episode, soft type/theme penalties)
   → pack size band ~20–30 before marketer (configurable top_n)

⑧ MARKETER TRIM                   [rule agent; LLM off in web path]
   marketer_agent on enriched pack cards
   → protect stars; hard-cut thin hooks; soft multi-fail rejects
   → target keep band typically 12–20
   → Priority UI list

⑨ DELIVER + UI
   final_deliverable.write_deliverable → JSON/CSV
   web loads last run into Priority / By episode / Continuity
```

### Web mode mapping (exact)

From `web/services/data_layer.py` when Generate runs:

| UI mode | `mini_arc_mode` | `scoring_mode` |
|---------|-----------------|----------------|
| **rule** | `rule` | `rule` |
| **hybrid** (default) | `rule` | `hybrid` |
| **llm** | `llm` | `llm` |

Even when UI selects `llm` for mini-arc, orchestrator still passes `llm_client=None` into validation, so mini-arc **falls back to rule heuristics** (see mini-arc LLM branch). Scoring still uses Groq when the key exists.

---

## 4. Architecture blocks — behavior and wiring

### Diagram (logical, code-accurate)

```
 scripts (.txt)
        │
        ▼
 ┌──────────────┐
 │   PARSER     │  scenes · beats · times · loglines
 └──────┬───────┘
        │
        ▼
 ┌──────────────────────────┐
 │ STORY WINDOW EXPANSION   │  ALWAYS rule structure
 │ ~15–60s hook→cliff spans │
 └──────┬───────────────────┘
        │
        ▼
 ┌──────────────────────────┐
 │ MINI-ARC VALIDATOR       │  live runs: rule only (client=None)
 └──────┬───────────────────┘
        │
        ▼
 ┌──────────────────────────┐
 │ SCORER + TYPE            │  rule | hybrid | llm
 │ (+ Groq if key present)  │
 └──────┬───────────────────┘
        │
        ▼
 ┌──────────────────────────┐
 │ PER-EP TOP-K SELECT      │  hook/cliff floor + time gap diversity
 └──────┬───────────────────┘
        │
        ├──────────────────────────────┐
        │                              │
        ▼                              ▼
 By-episode catalogue          FULL finals harvest
 (UI: By episode)                      │
                                       ▼
                            ┌─────────────────────┐
                            │ CONTINUITY MAP      │
                            └──────────┬──────────┘
                                       ▼
                            ┌─────────────────────┐
                            │ SERIES RANKER       │
                            │ global score +      │
                            │ diversity_pack      │
                            └──────────┬──────────┘
                                       ▼
                            ┌─────────────────────┐
                            │ MARKETER AGENT      │
                            │ protect / reject    │
                            └──────────┬──────────┘
                                       ▼
                               CAMPAIGN / PRIORITY
```

### Block notes

#### A. Parser (`src/parser.py`)
- Turns episode `.txt` into structured scenes/beats with timing.
- Also feeds series context / loglines used later in ranking cards.

#### B. Story windows (`src/candidate_generator.py`)
- Finds trigger moments, expands **backward and forward** into a natural window.
- Designed as storytelling spans (hook → cliff), including sub-windows inside long scenes.
- **Not** switched by scoring mode.

#### C. Mini-arc (`src/mini_arc_validator.py`)
- Rule heuristics check for complete mini-arc shape.
- Code supports `rule` / `llm` / `hybrid` (hybrid = rule first; LLM only if rule rejects **and** client exists).
- **Live orchestrator always passes `llm_client=None`**, so production behavior is rule validation.

#### D. Scorer (`src/llm_agents.py`)
- Metrics on **0–10**: hook, cliff, emotional escalation, narrative completeness, overall, etc.
- **rule:** deterministic heuristics for everyone.
- **hybrid:** rule scores everyone → LLM polishes **top N/ep** (`llm_per_episode`, default 5): `hook_type`, `reason`/`llm_rationale`, merge `promo_types`. **Numeric scores stay rule.**
- **llm:** rule baseline everyone → LLM **re-score** top N/ep (numbers can change). Failures keep rule score.
- **Fallback:** `client is None` → entire function stays on rule.

#### E. Per-episode select (`orchestrator.rank_and_select`)
- Drop very weak opens/ends (`hook_cliff_min=3.5`).
- Prefer candidates not stacked on the same few seconds (`min_gap_sec=4`).
- Keep `top_k` (product runs commonly use 5).

#### F. Continuity map (`src/series_continuity_map.py`)
- Built from processed episode inputs (not a hand-written bible).
- Spine themes, characters, arc phases, spoiler guidance, series one-liner.
- Used by fit / role / risk helpers in the ranker and shown in the Continuity UI.

#### G. Series ranker (`src/series_ranker.py`)

**Global score (exact weights in code):**

```
series_global_score =
    0.26 * overall
  + 0.16 * hook
  + 0.16 * cliff
  + 0.08 * emotional
  + 0.06 * narrative
  + 0.14 * continuity_fit
  + 0.10 * standalone_clarity
  + 0.04 * campaign_role_bonus
  + 0.04 * duration_fit
  - 0.06 * spoiler_risk
  + small bonuses:
        +0.20 if acquisition role AND clarity ≥ 7.0
        +0.12 if fit ≥ 8.0 AND hook ≥ 7.0
  clamped to 0–10
```

**Explicitly excluded from the formula:** `promo_types` / classification labels.

**Campaign role** (by episode position in the season): e.g. early = acquisition, late = payoff — soft bonus only, not a hard gate.

**Diversity pack** (`diversity_pack`):
- Default **max 2 promos per episode**
- Soft penalties for repeating primary type / theme / nearby episodes (not hard type bans)
- Pack target roughly **20–30** before marketer (`min_n=20`, `max_n=30`, optional `top_n`)

#### H. Marketer (`src/marketer_agent.py`)

Runs **after** cards are enriched (real hook/cliff text), not on raw stubs.

**Protect (examples of thresholds in code):**
- Top **10** pack slots  
- `series_global_score ≥ 7.85`  
- `overall ≥ 8.0` with clarity ≥ 6.5 and non-thin hook  
- strong craft + clarity combos  
- strong acquisition keepers  

**Hard cuts (can override protect):**
- Thin / empty hook  
- Degenerate segments  
- Stage-direction hook (unless very strong protected exception)

**Other fails / soft flags (unprotected):**
- Thin cliff, duration outside **14–62s**, low overall/global/clarity  
- Weak fit+clarity, late payoff unclear for cold traffic, etc.  
- Multi-fail / fail+soft combinations → cut  
- If still oversized: drop lowest unprotected first toward **min_keep–max_keep** (web: **12–20**)

**Types do not drive marketer keep/cut.**  
Web path: `marketer_use_llm=False` (pure rule marketer).

#### I. Deliverable + Web
- `final_deliverable.write_deliverable`:  
  - **Layer A:** campaign pack from **full finals**  
  - **Layer B:** per-episode champions for catalogue ordering  
  - Exports JSON/CSV under `output/final` and/or project `output/`  
- Web projects isolate scripts + results; support create / activate / delete  
- **Generate** = write new artifacts; **open project** = read last save  

---

## 5. Full pipeline diagram (one page)

```
                    Episode scripts (.txt)
                              │
              ① PARSE         ▼
                    scenes · beats · timestamps
                              │
              ② WINDOWS       ▼
                 story windows (ALWAYS rule)
                              │
              ③ MINI-ARC      ▼
                 valid mini-stories (rule in live runs)
                              │
              ④ SCORE         ▼
         ┌────────────────────────────────────┐
         │ rule | hybrid★ | llm               │
         │ ★ default                          │
         │ hybrid = rule numbers + LLM polish │
         │ llm    = LLM re-score top-N/ep     │
         │ no key = rule                      │
         └────────────────┬───────────────────┘
                          │
              ⑤ TOP-K     ▼
              per-episode finals (hook/cliff floor + gap diversity)
                          │
            ┌─────────────┴──────────────┐
            ▼                            ▼
     BY EPISODE UI              FULL FINALS POOL
                                     │
                         ⑥ CONTINUITY MAP
                                     │
                         ⑦ GLOBAL SCORE + DIVERSITY PACK
                            (max 2/ep, soft type/theme penalties)
                                     │
                         ⑧ MARKETER PROTECT / REJECT
                            (keep ~12–20)
                                     │
                         ⑨ PRIORITY UI + exports
```

---

## 6. Concepts — definition, why, real-life parallel

| Concept | In this system | Why | Studio parallel |
|---------|----------------|-----|-----------------|
| **Story window** | Timed multi-beat span | Promos need lead-in + land | Editor in/out |
| **Mini-arc** | Hook → escalation → cliff check | Drop fragments | “Does the trailer *play*?” |
| **Hook / cliff scores** | 0–10 open/end strength | Scroll-stop + open loop | First-line / button test |
| **Overall / emotion / narrative** | Local quality dims | Single metric lies | “Does it hit?” |
| **Promo type** | Tag(s) | Browse + soft pack diversity | Board labels |
| **Type ≠ score gate** | Not in global formula | Don’t kill strong oddballs | Marketer overrides taxonomy |
| **By-episode Top‑K** | Best local windows | Full catalogue | Episode pull list |
| **Finals harvest** | All Top‑K across eps | Input to campaign ranking | Shared drive pool |
| **series_global_score** | Feed usefulness | Local ≠ global | Weekly content plan |
| **Continuity fit** | Overlap with show spine | Sell *this* title | “Sounds like our series” |
| **Standalone clarity** | Cold-audience readability | Social is mostly cold | Stranger hallway test |
| **Campaign role** | Early acquire / late payoff | Soft positional prior | Launch vs re-engagement ads |
| **Spoiler risk** | Soft penalty | Protect long-arc mystery | “Don’t burn ep 40 in a reel” |
| **Diversity pack** | Cap per ep + soft repeats | Avoid one-note feed | Content calendar balance |
| **Marketer protect** | Lock strong rows | Stop over-trim | “This one’s sacred” |
| **Marketer reject** | Drop thin/risky/redundant | Usable shortlist | Kill meeting |
| **Hybrid mode** | Rule core + LLM polish | Taste + reliability + cost | Junior cut + senior copy polish |
| **Project isolation** | Per-show scripts/outputs | No cross-talk | Separate series drives |

---

## 7. Scoring modes: Rule · Hybrid · LLM

### What the code actually does

| Mode | Numeric scores | LLM used for | Cost / risk | Fallback |
|------|----------------|--------------|-------------|----------|
| **rule** | Heuristics for all candidates | Nothing | Free, fast, deterministic | n/a |
| **hybrid** ★ default | **Same rule numbers** | Top‑N/ep: hook_type, reason, promo_types | Bounded LLM spend | No key / errors → pure rule |
| **llm** | Rule baseline; **LLM overwrites top‑N/ep** | Full score pass on top‑N/ep | Highest latency + tokens | Failed calls keep rule score |

Always: **rule-score everyone first**, then optionally spend LLM only on the best `llm_per_episode` (default **5**) per episode, with small concurrency.

Window expansion stays rule in all modes. Mini-arc is rule in live orchestrator runs.

### Why Hybrid is the default

1. **Reliability** — Works without `GROQ_API_KEY` (identical rule floor).  
2. **Bounded cost** — LLM only on top‑N per episode, polish not full re-rank.  
3. **Better cards when API is healthy** — Human-readable reasons / types improve review UX.  
4. **Honest degradation** — Quota/errors → still ship rule output (seen in mode report when TPD exhausted).  
5. **Evidence** — Full 1–50 harvest comparison documented separately.

### Deep comparison (reference)

**📄 [output/full_compare/MODE_REPORT.md](../output/full_compare/MODE_REPORT.md)**

That report covers raw/validated/final counts, score means, overlap, unique finds, and the practical recommendation tree. Use it when you want experiment detail; this overview stays on **architecture + code behavior**.

### Product UI

- Toggle: **rule / hybrid (Recommended) / llm**  
- Generate runs the mapping table in §3  
- “Load demo results” reads cached mode packs for inspection without a live run  

---

## 8. What a user actually experiences

1. **Create project** → upload episode scripts  
2. Choose mode (default **hybrid**)  
3. **Generate** → real pipeline writes harvest + campaign into the project  
4. **Priority** → marketer-trimmed global pack (hook / cliff / why / scores)  
5. **By episode** → Top‑K catalogue inside each episode  
6. **Continuity** → map the ranker used  
7. Export / review; **delete** projects when done  

Opening a project later **reloads saved outputs**; it does not silently re-score the whole series.

---

## 9. Scope honesty (prototype boundary)

**Solid and real in code today**
- End-to-end storytelling window pipeline  
- Dual layers (episode catalogue + campaign pack from full finals)  
- Continuity-aware global score with documented weights  
- Rule marketer protect/reject with explicit thresholds  
- Web projects, generate, load, delete  
- Mode switch with true rule fallback  
- Experiment artifact comparing modes on eps 1–50  

**Prototype-shaped / limitations**
- Mini-arc LLM/hybrid branches exist but are **not client-wired** in `run_targeted_pipeline`  
- Hybrid does **not** mean “LLM re-ranks all scores”; it means **rule scores + LLM copy/type polish** on top‑N  
- Continuity / clarity / spoiler helpers are heuristic (keyword/spine based), not a full narrative model  
- Some theme/taxonomy flavor can be show-biased  
- LLM quality depends on keys, quotas, latency  
- Human taste remains final authority  

Treat it as a **studio copilot**: tireless episode coverage, explicit ranking, inspectable shortlist.

---

## 10. Code map

| Area | Primary location |
|------|------------------|
| Orchestration | `src/orchestrator.py` (`run_targeted_pipeline`) |
| Parse | `src/parser.py` |
| Windows | `src/candidate_generator.py` |
| Mini-arc | `src/mini_arc_validator.py` |
| Score / modes | `src/llm_agents.py` (`run_scoring_and_classification`, `hybrid_score_candidate`) |
| Continuity | `src/series_continuity_map.py` |
| Global rank + pack | `src/series_ranker.py` |
| Marketer | `src/marketer_agent.py` |
| Deliverable | `src/final_deliverable.py` |
| Web generate / projects | `web/services/data_layer.py`, `web/app.py`, `web/static/` |
| Mode comparison report | `output/full_compare/MODE_REPORT.md` |
| Decision log | `DECISIONS.md` |

---

## 11. Verification method

This document was checked against:

- `run_targeted_pipeline` step order and `llm_client=None` on mini-arc  
- `run_scoring_and_classification` mode branches and hybrid polish fields  
- `compute_global_score` weight lines  
- `build_campaign_pack` / `diversity_pack` inputs (full `finals`)  
- `marketer_agent` protect/cut constants and web `marketer_use_llm=False`  
- Project generate path in `data_layer` (parse → pipeline → deliverable → load)  

If code changes, update the **truth table in §0** first, then the narrative sections.

---

*Purpose: any reader — product, engineer, or studio partner — should see first principles, the real-world parallel, and the machinery **as implemented**, without reverse-engineering the repo or over-trusting marketing language.*
