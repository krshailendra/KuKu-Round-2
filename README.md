# KuKu \| Find the Promos

**Working prototype:** [Open Find the
Promos](https://kuku-promo-finder-2m3o.onrender.com/)

**Default mode:** Hybrid\
**Outputs:** By-episode catalogue and Campaign Priority pack

------------------------------------------------------------------------

## 1. The problem and the approach

A show has only a few seconds in the feed to earn someone's attention. A
short clip needs to stop the scroll, tell a small but complete story,
and leave the viewer wanting more. Picking those moments by hand across
roughly 50 episodes is slow and inconsistent. It can also favour
whichever episodes an editor watched most recently.

The task is not simply to find dramatic lines. It is to find clips that
are ready to publish, then decide which ones the show should promote
first.

### The audience insight

A viewer usually does not care whether a compelling moment comes from
the pilot or episode 30. If the clip works on its own, the viewer may be
more likely to explore the series. A cold audience responds to a feeling
and an unanswered question, not a plot explanation.

For that reason, the system looks for self-contained mini-stories that
still feel true to the series, rather than trailers made only from
opening scenes or collections of disconnected dialogue.

## 2. Assumptions when information is incomplete

The brief leaves a few operational questions open. The system uses the
following working assumptions:

-   Scripts are the source of truth for structure and timing. Video
    comes later in the workflow.
-   Most viewers are new to the show, so a clip must be clear on its own
    as well as dramatic.
-   The target is a 15 to 60 second storytelling window. Pack quality
    checks allow roughly 14 to 62 seconds.
-   There are two separate questions and therefore two lists: what is
    best within an episode, and what the show should post first.
-   Labels are tags, not filters. A strong moment should not be rejected
    just because its type is unusual.
-   API keys and quotas can disappear. The default workflow must still
    run on rules and fall back cleanly.
-   Each project represents one show. People remain responsible for the
    final publishing decision.

## 3. How the solution works

The workflow follows the way a studio team would work: the editor marks
moments in each episode, a pool of candidates builds up, series context
helps judge them, the growth team ranks the campaign, the marketer
protects the strongest clips and removes weak ones, and the board gives
the team a place to review the result.

**Studio workflow:** Editor finds windows and mini-arcs; scorer assesses
quality and types; producer maintains the continuity map; growth ranks
across the series; marketer protects strong clips and rejects weak ones;
board reviews the web UI.

### Pipeline: from scripts to a promo pack

``` mermaid
flowchart LR
    A["1. Parse<br/>Scripts to scenes,<br/>beats and timings"]
    B["2. Windows<br/>Expand around triggers,<br/>15–60 sec"]
    C["3. Mini-arc<br/>Hook → build → cliffhanger"]
    D["4. Score + type<br/>Rules for all;<br/>LLM polish top-N"]
    E["5. Top-K / episode<br/>Keep strongest,<br/>spaced moments"]
    F["6. Continuity<br/>People, themes,<br/>arc and spoilers"]
    G["7. Series rank<br/>Global score and<br/>diversity pack"]
    H["8. Marketer<br/>Protect, reject<br/>and trim to 12–20"]

    A --> B --> C --> D
    D --> E --> F --> G --> H
```

One candidate pool feeds two outputs: the **By-episode catalogue** and
the **Campaign Priority pack**.

The search coverage does not shrink when the mode changes. Window
generation stays rule-based, which keeps it complete and inexpensive.

### How each stage works

1.  **Parse:** Scripts become scenes and beats with characters, dialogue
    and timestamps. The system works with timed ranges, not loose
    quotes.
2.  **Windows:** Trigger-based expansion always runs through rules. It
    searches backwards and forwards to form 15 to 60 second storytelling
    spans. The mode does not reduce coverage.
3.  **Mini-arc gate:** A candidate must have a hook, rising pressure and
    a cliffhanger. The live path uses the fast rule validator. The LLM
    mini-arc code is ready for paid capacity, but is not live yet.
4.  **Score and type:** The rule baseline scores hook, cliff, emotion,
    narrative and overall quality from 0 to 10, and assigns types.
    Hybrid keeps the rule scores and uses the LLM to improve the reason,
    hook type and types for the top candidates per episode. LLM mode may
    re-score that shortlist. If the key is missing or a call fails, the
    system uses rules. Weak long-tail candidates are not sent to an LLM.
5.  **Top-K per episode:** The system sets minimum quality floors for
    openings and endings, prefers moments that are spaced apart, and
    keeps the Top-K, often five. These candidates feed both the episode
    catalogue and the campaign pool.
6.  **Continuity:** A show-specific map tracks people, recurring themes,
    story phases and spoiler guidance. It is living context, not a fixed
    handbook for one title.
7.  **Series ranking:** The global score combines quality, hook and
    cliff strength, continuity fit, clarity, role and duration, while
    penalising spoilers. Types are excluded from the formula. Diversity
    limits the pack to at most two clips per episode and softly spaces
    types and themes, producing a shortlist of around 20 to 30.
8.  **Marketer:** In the web workflow, the marketer uses enriched hook
    and cliff text. It protects top and high-global-score rows, removes
    thin hooks and broken segments, drops candidates with several soft
    failures, and trims the pack to roughly 12 to 20 Priority clips.

**Global score weights in code:** 0.26 overall, 0.16 hook, 0.16 cliff,
0.08 emotion, 0.06 narrative, 0.14 continuity fit, 0.10 clarity, 0.04
role, 0.04 duration and -0.06 spoiler, with small acquisition and fit
bonuses.

### Two outputs from one pool

The **By-episode catalogue** shows the best windows inside each episode
and supports the editor archive through `rank_and_select`.

The **Campaign Priority pack** answers what the show should post first,
using global score, diversity and marketer review. Generate writes the
artifacts; reopening a project reloads the last save and does not
silently re-score the full catalogue.

## 4. How the design evolved

The first AI-generated drafts leaned towards putting a smart agent at
every step. That looks neat on a whiteboard, but becomes expensive and
slow across a full season. These are the approaches considered and what
each taught us:

  -----------------------------------------------------------------------
  Approach                What was tried          Decision
  ----------------------- ----------------------- -----------------------
  Agent per step          A sequential LLM chain  Latency and cost grow
                          for expansion,          quickly. Keep structure
                          validation, scoring,    rule-first instead of
                          classification and      running an agent chain
                          ranking.                for every beat.

  Rules only              Heuristics from start   Coverage and uptime are
                          to finish.              strong, but promo cards
                                                  can feel flat. Add
                                                  optional LLM polish.

  Full LLM scoring        Let the model judge     The quality ceiling can
                          every candidate.        be high, but keys and
                                                  quotas make it
                                                  unreliable. It is also
                                                  excessive for the long
                                                  tail.

  Hybrid, selected        Rule core with LLM      The product always has
                          polish on the top       a working path,
                          candidates per episode, spending stays bounded,
                          or re-scoring in LLM    and review cards
                          mode.                   improve when the API is
                                                  available.

  Types as filters        Reject candidates early This hides strong but
                          if they do not match a  unusual moments. Types
                          preferred genre or      remain tags; the score
                          type.                   ignores them and pack
                                                  diversity handles them
                                                  softly.

  One ranked list         Use one scoreboard for  This mixes up the
                          the whole interface.    episode archive and the
                                                  campaign feed. Keep a
                                                  By-episode catalogue
                                                  and a separate Priority
                                                  pack.
  -----------------------------------------------------------------------

## 5. Rule, Hybrid and LLM modes

  -----------------------------------------------------------------------
  Mode              Scores            LLM role          Best use
  ----------------- ----------------- ----------------- -----------------
  **Rule**          All heuristic     None              Bulk processing,
                    scores                              offline use or
                                                        zero spend.

  **Hybrid          Rule scores stay  Polishes the      Default product
  (default)**       in place          reason, types and path, with
                                      hook type for the automatic
                                      top candidates    fallback.
                                      per episode.      

  **LLM**           May re-score the  Full scoring pass Paid capacity and
                    top candidates    on the shortlist. a launch-time
                    per episode                         taste pass.
  -----------------------------------------------------------------------

### Why Hybrid is the default

A promo tool that stops working when an API key is missing is not
dependable. The rule-based floor runs on every window, and tokens are
spent only on the few candidates people are likely to review. If Groq is
unavailable or rate-limited, the system falls back cleanly.

A head-to-head comparison across episodes 1 to 50 is available in the
[Mode
Report](https://drive.google.com/file/d/1fPPMLSv_8rjgF2djTgsvUPVCmrSMRsBA/view?usp=drive_link).

### Using paid LLM capacity without rebuilding the system

Scoring uses Groq when `GROQ_API_KEY` is present. Free and low-tier
limits are enough for Hybrid polish, but full-season LLM mode runs into
requests-per-minute, tokens-per-minute and daily caps. Quota-related
degradation has already been observed.

-   **Groq paid or higher limits:** Performance or Batch-style capacity
    can raise concurrency and `llm_per_episode`, allow a larger
    shortlist to be re-scored, and enable the existing LLM or Hybrid
    mini-arc check for borderline structure. Fast open-weight models
    keep the cost of a 50-episode harvest manageable.
-   **Batch or Flex-style processing:** Groq Batch or OpenAI Batch,
    which is roughly half the real-time price, can run overnight scoring
    and mini-arc checks across the full catalogue. The packs can then be
    ready in the morning, which suits weekly operations across shows.
-   **Frontier model:** Use an OpenAI or Anthropic model only on the
    final Priority shortlist of around 20 to 30 clips. It can improve
    brand voice, spoiler nuance and copy quality after rule-based
    harvesting and global ranking. It should not process thousands of
    raw windows.
-   **Keep the rule-first foundation:** Window expansion and long-tail
    processing remain rule-based. Paid LLM capacity should improve
    judgment on the shortlist, not bring back sequential agents for
    every beat.

## 6. Scaling to every show

The product structure stays the same while the content changes from
title to title. Each project keeps its own scripts and outputs, with
create, generate and delete actions, so one app can support many shows.

New content enters through the scene and beat structure, without
requiring a new technology stack. Continuity is built from that show's
own episodes. Campaign role can also reflect season length, with early
episodes given a soft acquisition prior and later episodes a soft payoff
prior.

The two operator views remain By-episode and Priority. As the range of
genres grows, each show can get a light theme vocabulary and gold
evaluation slices. This localises memory and evaluation rather than
creating a separate pipeline for every genre.

## 7. How we know it is working

Each promo is represented as a window with a hook, cliff, rationale,
scores and campaign context. The result is something a teammate can
evaluate and discuss, not just a list of keywords.

The two lists are separate paths in the implementation: episode-level
Top-K and the full-finals campaign pack followed by marketer review.
Mode comparisons across episodes 1 to 50 measure agreement, unique finds
and quota-related degradation.

The `evaluation/` folder supports gold-style checks beyond judging the
interface by appearance. The web Generate action runs the actual
orchestrator and deliverable writers, so what appears in the UI matches
the objects the system produces.

A teammate should be able to open Priority, understand why the first
clip ranks first, check episode coverage in By-episode, review
Continuity and export the results without relying on an informal
spreadsheet.

## 8. How AI was used, and where it got things wrong

Grok (xAI) was the main implementation partner for refactoring, the web
UI, mode wiring, marketer and ranker iterations, and documentation.
Suggestions were checked against the source code rather than assuming
the generated explanation was correct.

-   **Sequential agents everywhere:** Early suggestions used an LLM
    chain to expand, validate, score, classify and rank every candidate.
    That would be too slow across full seasons, so structure stayed
    rule-based and LLM use was limited to polishing the top candidates.
-   **Score-only or pure-LLM defaults:** AI tended to reduce a good
    promo to one scoreboard or to rely entirely on model judgment. Both
    approaches were tried, but neither was right as the product default.
    Hybrid gave the system uptime, a real fallback and better polish
    when available.
-   **Types as hard filters:** This was convenient for a demo but not
    useful for growth. Types were kept as tags and left out of the
    global scoring formula.
-   **Overstated documentation:** Early drafts said Hybrid re-scored the
    model's judgment and that LLM mini-arc validation was live. A code
    audit corrected both claims. Hybrid currently polishes copy and
    types; the live mini-arc check is rule-based. The code, not the
    wording, is the source of truth.
-   **UI scope creep:** A narrow request, such as adding a
    project-delete control, sometimes led the agent to rewrite unrelated
    parts of the interface. Changes were kept focused and limited in
    scope.

**Approach:** AI helped speed up implementation, while the architecture,
constraints and checks against the actual implementation remained human
responsibilities.

## 9. What is solid today, and what comes next

### Working today

-   End-to-end storytelling windows.
-   Separate catalogue and campaign layers.
-   Continuity-aware global ranking with explicit weights.
-   Marketer protection and rejection.
-   A project-based web app.
-   Hybrid mode with genuine rule fallback.
-   Mode comparison across the full 1 to 50 episode harvest.

### Next improvements

-   Enable LLM mini-arc checks for borderline candidates when paid
    capacity is available.
-   Run overnight batch taste passes across the catalogue.
-   Use a frontier model only on the final Priority shortlist.
-   Build genre-specific continuity vocabularies and gold sets.
-   Improve timing robustness.
-   Add an optional handoff to editing tools.

------------------------------------------------------------------------

**In short:** Promos should work as mini-stories. The episode catalogue
and campaign pack serve different jobs. Hybrid is the dependable
default, while paid LLM capacity can improve the shortlist without
slowing the whole pipeline with agent chains. Grok helped speed up
implementation; the product decisions, constraints and code checks
remained human-led.
