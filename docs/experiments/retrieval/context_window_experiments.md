# Retrieval Context Window Experiments

**Goal**: Find an optimal context window strategy for the three retrieval agents that is:
- Effective for the current script ("I Married a Broken Soldier...")
- Generalizable to other scripts (not overfit to one story)
- Efficient (avoids unnecessary tokens while giving enough signal)

---

## Initial Decision (v1)

Date: 2025-04-06
Agent: GrokCode

### Context Windows Chosen

| Agent                    | Beats Before | Current | Beats After | Total Beats | Rationale |
|--------------------------|--------------|---------|-------------|-------------|-----------|
| `SceneContextAgent`      | 3            | Yes     | 2           | 6           | Needs to understand tone, emotional arc, and pacing. Requires both backward and forward context to detect scene type and mood shifts. |
| `LuxurySignalAgent`      | 1            | Yes     | 0           | 2           | Focused on detecting natural luxury/brandable moments. Too much surrounding context can dilute whether the current line itself carries a subtle brand signal. Only needs immediate prior beat for flow. |
| `ImmersionRiskAgent`     | 2            | Yes     | 3           | 6           | Highest context need. Must judge emotional intensity and whether inserting a promo would break immersion. Forward context (next beats) is critical to see if the moment is high-stakes, quiet, or transitional. |

### Shared Context (sent to all agents)
- Episode logline
- Character name + emotion (if available)
- Beat index + timestamp (if available)
- Full text of beats in the window

### Design Principles Applied
1. **Role-based context** — Not every agent gets the same window.
2. **Asymmetric windows** — `ImmersionRiskAgent` is forward-heavy because future beats reveal consequences of breaking immersion.
3. **Minimal viable context** — `LuxurySignalAgent` is deliberately narrow to avoid noise.
4. **Generalizability** — Windows are defined in relative beats (not hardcoded lines), so they work across different episode lengths and formats.

---

## Experiment Plan

We will run experiments on at least 3–5 episodes and track:

| Experiment ID | Change Tested                          | Metrics to Track                          | Decision Criteria |
|---------------|----------------------------------------|-------------------------------------------|-------------------|
| EXP-001       | Current v1 windows                     | Signal quality, false positives, noise    | Baseline |
| EXP-002       | Give `LuxurySignalAgent` +1 after beat | Does it improve or add noise?             | Compare precision |
| EXP-003       | Reduce `ImmersionRiskAgent` to 2 after | Does forward context matter this much?    | Check immersion accuracy |
| EXP-004       | Give all agents identical wide window  | Token cost vs quality trade-off           | Only accept if big quality gain |
| EXP-005       | Test on a different genre script       | Generalization performance                | Must not degrade significantly |

**Success Criteria for General Purpose**:
- Works reasonably on both drama/romance (current script) and at least one other genre (action, thriller, comedy, etc.).
- Token usage stays under ~1200–1500 tokens per agent call on average.
- Retrieval quality doesn't drop more than 15% when moving to a new script.

---

## Notes / Observations

- [ ] Run first experiment after Groq key is integrated
- [ ] Track actual token usage per agent
- [ ] Log any cases where context was clearly insufficient or excessive

---

**Current Status**: v1 decision logged + **FULLY IMPLEMENTED + IMPROVED**

### Improvements Made (this session)
- Switched to **async Groq client** (`AsyncGroq`) with `asyncio.gather`
- Agents now run **in parallel** per candidate (3 calls → 1 concurrent batch)
- Added semaphore (`MAX_CONCURRENT=6`) to respect free-tier rate limits
- Orchestrator now builds `_episodes_data` (flat beat lists) and passes it to agents
- Context windows (`scene_context`, `luxury_signal`, `immersion_risk`) are now **actually used**
- Proper `(episode, scene) → beat_index` mapping added
- Sync wrapper kept for backward compatibility

### Files Changed
- `src/llm_agents.py` — full async rewrite + parallel orchestration
- `src/orchestrator.py` — builds episode beat data + passes to agents
- `.env`, `.env.example`, `.gitignore` — secure key handling

Ready for first real run on episodes.