# Find the Promos — Final Deliverable

> Per promo: **episode**, **ordered segment timestamps**, **hook**, **cliffhanger**, **why it works**. Campaign pack ranked with **Series Continuity Map** + global score (classification labels are tags only).

**Mode:** `hybrid`
**Episodes covered:** 50
**Global pool size:** 182
**Campaign pack N:** 25 (user) — user-requested N=25 then marketer trim

## 0. Series Continuity Map

Whole-series context built from **all episode inputs** (50 eps). Used for fit/clarity — **not** to force one promo type.

> Lady Juliana arrives at the cathedral in her late mother's bridal gown, only to suffer the ultimate betrayal when her fiancé Gerald abandons her at the altar for her cruel sister C Dominant threads: Central bond (Juliana ↔ Alexander), Wedding / betrayal, Identity / lineage, Violence / peril.

**Spine themes:** Central bond (Juliana ↔ Alexander) (central_bond), Wedding / betrayal (wedding_betrayal), Identity / lineage (identity_lineage), Violence / peril (violence_peril), Power / disownment (power_disownment), Secret / truth reveal (secret_truth)

**Principals:** Julianax692, Alexanderx334, Catherinex203, Geraldx74, Clarissax48, Agnesx20, Matriarchx17

Artifact: `data/processed/series_continuity_map.json`

## How ranking works

- **Continuity Map:** Series Continuity Map: built from all episode loglines + beat text; spine themes, principals, arc phases. Not used as a type filter.
- **Global Pool:** ALL hybrid final promos (top-k per ep), not only 1/ep champions
- **Series Global Score:** 0.26*overall + 0.16*hook + 0.16*cliff + 0.08*emotional + 0.06*narrative + 0.14*continuity_fit + 0.10*standalone_clarity + 0.04*campaign_role + 0.04*duration_fit - 0.06*spoiler_risk. promo_types / classification labels are EXCLUDED from the score.
- **Campaign Pack:** Take top N by global score with soft diversity (type mix, theme mix, ep spacing, max 2/ep). N user-set or auto in [20,30] via score floor + elbow + high-score richness.
- **Per Episode Catalogue:** max overall_score (then hook, cliff, duration) among hybrid top-k — for episode pages / assignment 'best per ep'
- **Marketer Note:** Classification labels stay on cards so marketers can experiment with all kinds; ranking never prefers one label over another.

**Type mix in pack (tags only):** {'emotional': 11, 'cliffhanger': 16, 'thrilling': 4, 'revelation': 10, 'romantic': 8, 'conflict': 3}

**Continuity theme mix:** {'wedding_betrayal': 11, 'violence_peril': 11, 'rival_court': 7, 'central_bond': 15, 'secret_truth': 5, 'identity_lineage': 15, 'power_disownment': 6, 'home_garden': 5}

**Marketer Agent:** kept 21 / pre 25 (cut 4, protected 19)

### Marketer cuts (removed from campaign pack)

- ep 21 old#14 g=7.373: CUT:soft_short_hook — "His skin is burning hot."
- ep 26 old#18 g=7.247: CUT:relative_pack_size — "Who are you? Speak to me. I have not seen your face before.
- ep 7 old#20 g=7.153: CUT:relative_pack_size — "This is where you live now?"
- ep 37 old#22 g=7.087: CUT:relative_pack_size — "After what she has been accused of? Of course."

---

## A. Campaign pack — post these first (global rank)

| Rank | Ep | Global | Role | Types (tag) | Themes | Start → End | Dur | Hook |
|-----:|---:|-------:|------|-------------|--------|-------------|----:|------|
| 1 | 3 | 8.68 | acquisition | emotional,cliffhange | wedding_betrayal,violence_pe | 00:00.000 → 00:22.500 | 22.5s | I didn't steal what was never truly y… |
| 2 | 32 | 8.616 | climax | emotional,cliffhange | central_bond,wedding_betraya | 01:47.200 → 02:22.400 | 35.2s | "And a woman who never embarrasses th… |
| 3 | 35 | 8.401 | climax | cliffhanger,revelati | secret_truth,identity_lineag | 02:02.000 → 02:37.500 | 35.5s | "I survived because the men who came … |
| 4 | 44 | 8.485 | payoff | emotional,cliffhange | central_bond,identity_lineag | 00:28.400 → 01:05.000 | 36.6s | "Do you know what this did to me?" |
| 5 | 11 | 8.465 | bonding | cliffhanger,revelati | central_bond,violence_peril, | 00:18.500 → 00:53.600 | 35.1s | "Your husband stole my gold pocket wa… |
| 6 | 35 | 8.531 | climax | emotional,cliffhange | secret_truth,identity_lineag | 01:11.500 → 02:05.500 | 54.0s | "Then how did you survive?" |
| 7 | 2 | 8.383 | acquisition | emotional,revelation | wedding_betrayal,rival_court | 00:34.300 → 01:09.300 | 35.0s | "Surely you will not let him humiliat… |
| 8 | 9 | 8.149 | bonding | cliffhanger | identity_lineage,power_disow | 01:23.800 → 01:55.500 | 31.7s | "Then we will face it together." |
| 9 | 21 | 8.46 | escalation | emotional,cliffhange | identity_lineage,violence_pe | 01:16.000 → 01:54.000 | 38.0s | "Keep him warm. Give him three drops … |
| 10 | 36 | 8.073 | climax | cliffhanger | power_disownment,wedding_bet | 01:00.900 → 01:39.000 | 38.1s | "I trusted them." |
| 11 | 32 | 8.051 | climax | cliffhanger | central_bond,rival_court,ide | 00:41.000 → 01:17.600 | 36.6s | "No. Your cruelty does that for me." |
| 12 | 3 | 8.318 | acquisition | emotional,cliffhange | rival_court,wedding_betrayal | 01:48.800 → 02:25.750 | 37.0s | "...to remember your worth." |
| 13 | 14 | 8.337 | bonding | emotional,cliffhange | violence_peril,central_bond, | 00:01.000 → 00:38.500 | 37.5s | I found it. |
| 14 | 36 | 8.226 | climax | emotional,cliffhange | power_disownment,wedding_bet | 00:41.600 → 01:18.100 | 36.5s | "They declared me dead." |
| 15 | 5 | 7.486 | acquisition | conflict | identity_lineage,power_disow | 00:10.500 → 00:46.000 | 35.5s | "The vows are spoken, Father. I am hi… |
| 16 | 11 | 8.119 | bonding | cliffhanger | central_bond,violence_peril, | 00:00.000 → 00:32.800 | 32.8s | "Gerald? What are you doing here?" |
| 17 | 33 | 8.208 | climax | cliffhanger,revelati | identity_lineage,central_bon | 01:21.000 → 02:24.000 | 63.0s | She drew something around the bed, di… |
| 18 | 15 | 8.015 | bonding | emotional,revelation | central_bond,home_garden,vio | 00:08.500 → 00:46.400 | 37.9s | "Stop! What are you doing?!" |
| 19 | 26 | 7.936 | escalation | emotional,revelation | violence_peril,secret_truth, | 00:30.800 → 01:07.000 | 36.2s | "You... you are no common servant. Yo… |
| 20 | 5 | 7.542 | acquisition | conflict | identity_lineage,wedding_bet | 00:00.000 → 00:15.800 | 15.8s | You will not leave this church carryi… |
| 21 | 31 | 7.901 | climax | cliffhanger | identity_lineage,violence_pe | 00:21.000 → 00:59.000 | 38.0s | Everyone saw you. Everyone watched hi… |

### Campaign cards (detail)

#### #1 · Episode 3 · `00:00.000` → `00:22.500` (22.5s)

global=**8.68** · ep_score=7.86 · role=*acquisition* · tags=['emotional', 'cliffhanger', 'thrilling'] · spine=['wedding_betrayal', 'violence_peril', 'rival_court']

| Field | Value |
|-------|-------|
| **Hook** | I didn't steal what was never truly yours. |
| **Cliffhanger** | "Now it is mine." |
| **Why it works** | Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast; betrayal/power turn is instantly readable cold. |
| **Why post here** | Ep 3 · acquisition: cold-open fuel — works without binge homework. Continuity fit 10.0/10, clarity 8.3/10, spine=[wedding_betrayal, violence_peril, rival_court], tags=[emotional, cliffhanger, thrilling] (tags not scored), global=8.68. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 0.0 | 22.5 | Master in–out (cut this whole promo) |
| 2 | hook | 0.0 | 8.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 8.5 | 16.3 | Escalation · scene_1 |
| 4 | cliffhanger | 16.3 | 22.5 | Cliffhanger (exit line) · scene_1 |

#### #2 · Episode 32 · `01:47.200` → `02:22.400` (35.2s)

global=**8.616** · ep_score=8.05 · role=*climax* · tags=['emotional', 'cliffhanger', 'revelation', 'romantic'] · spine=['central_bond', 'wedding_betrayal', 'violence_peril']

| Field | Value |
|-------|-------|
| **Hook** | "And a woman who never embarrasses the people standing behind her." |
| **Cliffhanger** | "...but you will never have the courage to earn what you demand from everyone else." |
| **Why it works** | Emotional/Cliffhanger beat (8.05/10): identity/lineage stakes land fast; intimacy and danger collide. |
| **Why post here** | Ep 32 · climax: peak tension for invested viewers. Continuity fit 9.57/10, clarity 7.8/10, spine=[central_bond, wedding_betrayal, violence_peril], tags=[emotional, cliffhanger, revelation, romantic] (tags not scored), global=8.616. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 107.2 | 142.4 | Master in–out (cut this whole promo) |
| 2 | hook | 107.2 | 119.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 119.5 | 131.8 | Escalation · scene_1 |
| 4 | cliffhanger | 131.8 | 142.4 | Cliffhanger (exit line) · scene_1 |

#### #3 · Episode 35 · `02:02.000` → `02:37.500` (35.5s)

global=**8.401** · ep_score=7.65 · role=*climax* · tags=['cliffhanger', 'revelation'] · spine=['secret_truth', 'identity_lineage', 'central_bond']

| Field | Value |
|-------|-------|
| **Hook** | "I survived because the men who came looking for me believed I was already dead." |
| **Cliffhanger** | "The men behind it... are the same men ruling Ashwood now." |
| **Why it works** | Cliffhanger/Revelation beat (7.65/10): identity/lineage stakes land fast. |
| **Why post here** | Ep 35 · climax: peak tension for invested viewers. Continuity fit 8.34/10, clarity 7.8/10, spine=[secret_truth, identity_lineage, central_bond], tags=[cliffhanger, revelation] (tags not scored), global=8.401. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 122.0 | 157.5 | Master in–out (cut this whole promo) |
| 2 | hook | 122.0 | 130.5 | Hook (opening lines) · scene_3 |
| 3 | rise | 130.5 | 140.5 | Escalation · scene_3 |
| 4 | cliffhanger | 140.5 | 157.5 | Cliffhanger (exit line) · scene_3 |

#### #4 · Episode 44 · `00:28.400` → `01:05.000` (36.6s)

global=**8.485** · ep_score=8.05 · role=*payoff* · tags=['emotional', 'cliffhanger', 'revelation', 'romantic'] · spine=['central_bond', 'identity_lineage', 'power_disownment']

| Field | Value |
|-------|-------|
| **Hook** | "Do you know what this did to me?" |
| **Cliffhanger** | "Did you?" |
| **Why it works** | Emotional/Cliffhanger beat (8.05/10): identity/lineage stakes land fast; intimacy and danger collide. |
| **Why post here** | Ep 44 · payoff: late-arc resonance — better after acquisition/bonding pack. Continuity fit 9.2/10, clarity 8.9/10, spine=[central_bond, identity_lineage, power_disownment], tags=[emotional, cliffhanger, revelation, romantic] (tags not scored), global=8.485. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 28.4 | 65.0 | Master in–out (cut this whole promo) |
| 2 | hook | 28.4 | 41.2 | Hook (opening lines) · scene_2 |
| 3 | rise | 41.2 | 53.0 | Escalation · scene_2 |
| 4 | cliffhanger | 53.0 | 65.0 | Cliffhanger (exit line) · scene_2 |

#### #5 · Episode 11 · `00:18.500` → `00:53.600` (35.1s)

global=**8.465** · ep_score=7.42 · role=*bonding* · tags=['cliffhanger', 'revelation'] · spine=['central_bond', 'violence_peril', 'home_garden']

| Field | Value |
|-------|-------|
| **Hook** | "Your husband stole my gold pocket watch!" |
| **Cliffhanger** | ...let the constable search." "Search it. |
| **Why it works** | Cliffhanger/Revelation beat (7.42/10): high-voltage delivery. |
| **Why post here** | Ep 11 · bonding: locks the central relationship so new viewers care. Continuity fit 10.0/10, clarity 7.1/10, spine=[central_bond, violence_peril, home_garden], tags=[cliffhanger, revelation] (tags not scored), global=8.465. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 18.5 | 53.6 | Master in–out (cut this whole promo) |
| 2 | hook | 18.5 | 28.9 | Hook (opening lines) · scene_1 |
| 3 | rise | 28.9 | 41.1 | Escalation · scene_1 |
| 4 | cliffhanger | 41.1 | 53.6 | Cliffhanger (exit line) · scene_1 |

#### #6 · Episode 35 · `01:11.500` → `02:05.500` (54.0s)

global=**8.531** · ep_score=8.05 · role=*climax* · tags=['emotional', 'cliffhanger', 'revelation'] · spine=['secret_truth', 'identity_lineage', 'central_bond']

| Field | Value |
|-------|-------|
| **Hook** | "Then how did you survive?" |
| **Cliffhanger** | "Then why did they never tell us?" |
| **Why it works** | Emotional/Cliffhanger beat (8.05/10): identity/lineage stakes land fast; open question pulls the next click. |
| **Why post here** | Ep 35 · climax: peak tension for invested viewers. Continuity fit 9.39/10, clarity 7.8/10, spine=[secret_truth, identity_lineage, central_bond], tags=[emotional, cliffhanger, revelation] (tags not scored), global=8.531. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 71.5 | 125.5 | Master in–out (cut this whole promo) |
| 2 | hook | 71.5 | 92.0 | Hook (opening lines) · scene_3 |
| 3 | rise | 92.0 | 106.0 | Escalation · scene_3 |
| 4 | cliffhanger | 106.0 | 125.5 | Cliffhanger (exit line) · scene_3 |

#### #7 · Episode 2 · `00:34.300` → `01:09.300` (35.0s)

global=**8.383** · ep_score=7.39 · role=*acquisition* · tags=['emotional', 'revelation', 'romantic', 'thrilling'] · spine=['wedding_betrayal', 'rival_court', 'identity_lineage']

| Field | Value |
|-------|-------|
| **Hook** | "Surely you will not let him humiliate me like this?" |
| **Cliffhanger** | "You should be grateful you're at least allowed to attend the wedding." |
| **Why it works** | Emotional/Revelation beat (7.39/10): identity/lineage stakes land fast; betrayal/power turn is instantly readable cold. |
| **Why post here** | Ep 2 · acquisition: cold-open fuel — works without binge homework. Continuity fit 10.0/10, clarity 8.9/10, spine=[wedding_betrayal, rival_court, identity_lineage], tags=[emotional, revelation, romantic, thrilling] (tags not scored), global=8.383. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 34.3 | 69.3 | Master in–out (cut this whole promo) |
| 2 | hook | 34.3 | 51.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 51.5 | 60.5 | Escalation · scene_1 |
| 4 | cliffhanger | 60.5 | 69.3 | Cliffhanger (exit line) · scene_1 |

#### #8 · Episode 9 · `01:23.800` → `01:55.500` (31.7s)

global=**8.149** · ep_score=7.22 · role=*bonding* · tags=['cliffhanger'] · spine=['identity_lineage', 'power_disownment', 'wedding_betrayal']

| Field | Value |
|-------|-------|
| **Hook** | "Then we will face it together." |
| **Cliffhanger** | "Impossible." |
| **Why it works** | Cliffhanger beat (7.22/10): identity/lineage stakes land fast. |
| **Why post here** | Ep 9 · bonding: locks the central relationship so new viewers care. Continuity fit 10.0/10, clarity 7.4/10, spine=[identity_lineage, power_disownment, wedding_betrayal], tags=[cliffhanger] (tags not scored), global=8.149. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 83.8 | 115.5 | Master in–out (cut this whole promo) |
| 2 | hook | 83.8 | 83.8 | Hook · scene_1 |
| 3 | cliffhanger | 83.8 | 115.5 | Cliffhanger · scene_2 |

#### #9 · Episode 21 · `01:16.000` → `01:54.000` (38.0s)

global=**8.46** · ep_score=7.86 · role=*escalation* · tags=['emotional', 'cliffhanger'] · spine=['identity_lineage', 'violence_peril', 'secret_truth']

| Field | Value |
|-------|-------|
| **Hook** | "Keep him warm. Give him three drops of this coltsfoot tea every morning." |
| **Cliffhanger** | "Inside that massive house with all their wealth, she is fading to nothing, and no one can stop it." |
| **Why it works** | Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast. |
| **Why post here** | Ep 21 · escalation: raises stakes mid-arc; binge bait after the open pack. Continuity fit 10.0/10, clarity 8.5/10, spine=[identity_lineage, violence_peril, secret_truth], tags=[emotional, cliffhanger] (tags not scored), global=8.46. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 76.0 | 114.0 | Master in–out (cut this whole promo) |
| 2 | hook | 76.0 | 90.8 | Hook (opening lines) · scene_3 |
| 3 | rise | 90.8 | 99.2 | Escalation · scene_3 |
| 4 | cliffhanger | 99.2 | 114.0 | Cliffhanger (exit line) · scene_3 |

#### #10 · Episode 36 · `01:00.900` → `01:39.000` (38.1s)

global=**8.073** · ep_score=7.22 · role=*climax* · tags=['cliffhanger'] · spine=['power_disownment', 'wedding_betrayal', 'identity_lineage']

| Field | Value |
|-------|-------|
| **Hook** | "I trusted them." |
| **Cliffhanger** | "Then where is she?" |
| **Why it works** | Cliffhanger beat (7.22/10): identity/lineage stakes land fast; intimacy and danger collide. |
| **Why post here** | Ep 36 · climax: peak tension for invested viewers. Continuity fit 10.0/10, clarity 7.8/10, spine=[power_disownment, wedding_betrayal, identity_lineage], tags=[cliffhanger] (tags not scored), global=8.073. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 60.9 | 99.0 | Master in–out (cut this whole promo) |
| 2 | hook | 60.9 | 74.7 | Hook (opening lines) · scene_1 |
| 3 | rise | 74.7 | 85.5 | Escalation · scene_1 |
| 4 | cliffhanger | 85.5 | 99.0 | Cliffhanger (exit line) · scene_1 |

#### #11 · Episode 32 · `00:41.000` → `01:17.600` (36.6s)

global=**8.051** · ep_score=7.22 · role=*climax* · tags=['cliffhanger'] · spine=['central_bond', 'rival_court', 'identity_lineage']

| Field | Value |
|-------|-------|
| **Hook** | "No. Your cruelty does that for me." |
| **Cliffhanger** | "I was freed. And I found a man who never asked me what I was worth." |
| **Why it works** | Cliffhanger beat (7.22/10): clean hook→pressure→turn inside a tight window. |
| **Why post here** | Ep 32 · climax: peak tension for invested viewers. Continuity fit 10.0/10, clarity 7.1/10, spine=[central_bond, rival_court, identity_lineage], tags=[cliffhanger] (tags not scored), global=8.051. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 41.0 | 77.6 | Master in–out (cut this whole promo) |
| 2 | hook | 41.0 | 52.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 52.5 | 67.0 | Escalation · scene_1 |
| 4 | cliffhanger | 67.0 | 77.6 | Cliffhanger (exit line) · scene_1 |

#### #12 · Episode 3 · `01:48.800` → `02:25.750` (37.0s)

global=**8.318** · ep_score=7.86 · role=*acquisition* · tags=['emotional', 'cliffhanger', 'romantic'] · spine=['rival_court', 'wedding_betrayal', 'identity_lineage']

| Field | Value |
|-------|-------|
| **Hook** | "...to remember your worth." |
| **Cliffhanger** | "Lady Juliana... accept my hand." |
| **Why it works** | Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast. |
| **Why post here** | Ep 3 · acquisition: cold-open fuel — works without binge homework. Continuity fit 7.49/10, clarity 8.2/10, spine=[rival_court, wedding_betrayal, identity_lineage], tags=[emotional, cliffhanger, romantic] (tags not scored), global=8.318. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 108.8 | 145.75 | Master in–out (cut this whole promo) |
| 2 | hook | 108.8 | 117.9 | Hook (opening lines) · scene_3 |
| 3 | rise | 117.9 | 129.9 | Escalation · scene_3 |
| 4 | cliffhanger | 129.9 | 145.75 | Cliffhanger (exit line) · scene_3 |

#### #13 · Episode 14 · `00:01.000` → `00:38.500` (37.5s)

global=**8.337** · ep_score=7.86 · role=*bonding* · tags=['emotional', 'cliffhanger', 'romantic', 'thrilling'] · spine=['violence_peril', 'central_bond', 'home_garden']

| Field | Value |
|-------|-------|
| **Hook** | I found it. |
| **Cliffhanger** | "You should never have had to bleed for me." |
| **Why it works** | Emotional/Cliffhanger beat (7.86/10): betrayal/power turn is instantly readable cold; intimacy and danger collide. |
| **Why post here** | Ep 14 · bonding: locks the central relationship so new viewers care. Continuity fit 8.75/10, clarity 8.9/10, spine=[violence_peril, central_bond, home_garden], tags=[emotional, cliffhanger, romantic, thrilling] (tags not scored), global=8.337. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 1.0 | 38.5 | Master in–out (cut this whole promo) |
| 2 | hook | 1.0 | 13.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 13.5 | 25.5 | Escalation · scene_1 |
| 4 | cliffhanger | 25.5 | 38.5 | Cliffhanger (exit line) · scene_1 |

#### #14 · Episode 36 · `00:41.600` → `01:18.100` (36.5s)

global=**8.226** · ep_score=7.86 · role=*climax* · tags=['emotional', 'cliffhanger'] · spine=['power_disownment', 'wedding_betrayal', 'identity_lineage']

| Field | Value |
|-------|-------|
| **Hook** | "They declared me dead." |
| **Cliffhanger** | "She went into Ashbourne Manor to save you. She never came back." |
| **Why it works** | Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast. |
| **Why post here** | Ep 36 · climax: peak tension for invested viewers. Continuity fit 10.0/10, clarity 7.2/10, spine=[power_disownment, wedding_betrayal, identity_lineage], tags=[emotional, cliffhanger] (tags not scored), global=8.226. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 41.6 | 78.1 | Master in–out (cut this whole promo) |
| 2 | hook | 41.6 | 51.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 51.8 | 63.8 | Escalation · scene_1 |
| 4 | cliffhanger | 63.8 | 78.1 | Cliffhanger (exit line) · scene_1 |

#### #15 · Episode 5 · `00:10.500` → `00:46.000` (35.5s)

global=**7.486** · ep_score=6.56 · role=*acquisition* · tags=['conflict'] · spine=['identity_lineage', 'power_disownment', 'wedding_betrayal']

| Field | Value |
|-------|-------|
| **Hook** | "The vows are spoken, Father. I am his wife now." |
| **Cliffhanger** | You chose that long before today. |
| **Why it works** | Conflict beat (6.56/10): identity/lineage stakes land fast. |
| **Why post here** | Ep 5 · acquisition: cold-open fuel — works without binge homework. Continuity fit 8.56/10, clarity 7.5/10, spine=[identity_lineage, power_disownment, wedding_betrayal], tags=[conflict] (tags not scored), global=7.486. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 10.5 | 46.0 | Master in–out (cut this whole promo) |
| 2 | hook | 10.5 | 20.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 20.8 | 36.5 | Escalation · scene_1 |
| 4 | cliffhanger | 36.5 | 46.0 | Cliffhanger (exit line) · scene_1 |

#### #16 · Episode 11 · `00:00.000` → `00:32.800` (32.8s)

global=**8.119** · ep_score=7.22 · role=*bonding* · tags=['cliffhanger'] · spine=['central_bond', 'violence_peril', 'rival_court']

| Field | Value |
|-------|-------|
| **Hook** | "Gerald? What are you doing here?" |
| **Cliffhanger** | "Of course you would defend him. You married a beggar!" |
| **Why it works** | Cliffhanger beat (7.22/10): open question pulls the next click; high-voltage delivery. |
| **Why post here** | Ep 11 · bonding: locks the central relationship so new viewers care. Continuity fit 10.0/10, clarity 7.1/10, spine=[central_bond, violence_peril, rival_court], tags=[cliffhanger] (tags not scored), global=8.119. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 0.0 | 32.8 | Master in–out (cut this whole promo) |
| 2 | hook | 0.0 | 10.7 | Hook (opening lines) · scene_1 |
| 3 | rise | 10.7 | 22.0 | Escalation · scene_1 |
| 4 | cliffhanger | 22.0 | 32.8 | Cliffhanger (exit line) · scene_1 |

#### #17 · Episode 33 · `01:21.000` → `02:24.000` (63.0s)

global=**8.208** · ep_score=7.24 · role=*climax* · tags=['cliffhanger', 'revelation'] · spine=['identity_lineage', 'central_bond', 'violence_peril']

| Field | Value |
|-------|-------|
| **Hook** | She drew something around the bed, did she not? |
| **Cliffhanger** | "I never said she was a witch!" |
| **Why it works** | Cliffhanger/Revelation beat (7.24/10): identity/lineage stakes land fast; open question pulls the next click. |
| **Why post here** | Ep 33 · climax: peak tension for invested viewers. Continuity fit 10.0/10, clarity 7.0/10, spine=[identity_lineage, central_bond, violence_peril], tags=[cliffhanger, revelation] (tags not scored), global=8.208. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 81.0 | 144.0 | Master in–out (cut this whole promo) |
| 2 | hook | 81.0 | 100.0 | Hook (opening lines) · scene_1 |
| 3 | rise | 100.0 | 123.5 | Escalation · scene_1 |
| 4 | cliffhanger | 123.5 | 144.0 | Cliffhanger (exit line) · scene_1 |

#### #18 · Episode 15 · `00:08.500` → `00:46.400` (37.9s)

global=**8.015** · ep_score=7.39 · role=*bonding* · tags=['emotional', 'revelation', 'romantic', 'thrilling'] · spine=['central_bond', 'home_garden', 'violence_peril']

| Field | Value |
|-------|-------|
| **Hook** | "Stop! What are you doing?!" |
| **Cliffhanger** | "Get out of the way!" |
| **Why it works** | Emotional/Revelation beat (7.39/10): identity/lineage stakes land fast; physical peril raises binge urgency. |
| **Why post here** | Ep 15 · bonding: locks the central relationship so new viewers care. Continuity fit 10.0/10, clarity 7.5/10, spine=[central_bond, home_garden, violence_peril], tags=[emotional, revelation, romantic, thrilling] (tags not scored), global=8.015. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 8.5 | 46.4 | Master in–out (cut this whole promo) |
| 2 | hook | 8.5 | 22.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 22.5 | 34.0 | Escalation · scene_1 |
| 4 | cliffhanger | 34.0 | 46.4 | Cliffhanger (exit line) · scene_1 |

#### #19 · Episode 26 · `00:30.800` → `01:07.000` (36.2s)

global=**7.936** · ep_score=7.6 · role=*escalation* · tags=['emotional', 'revelation'] · spine=['violence_peril', 'secret_truth', 'central_bond']

| Field | Value |
|-------|-------|
| **Hook** | "You... you are no common servant. You took Catherine's whip for me the other day." |
| **Cliffhanger** | "Yes. But the charcoal is fighting the poison. You are safe now." |
| **Why it works** | Emotional/Revelation beat (7.6/10): identity/lineage stakes land fast. |
| **Why post here** | Ep 26 · escalation: raises stakes mid-arc; binge bait after the open pack. Continuity fit 8.16/10, clarity 7.1/10, spine=[violence_peril, secret_truth, central_bond], tags=[emotional, revelation] (tags not scored), global=7.936. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 30.8 | 67.0 | Master in–out (cut this whole promo) |
| 2 | hook | 30.8 | 39.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 39.8 | 55.8 | Escalation · scene_1 |
| 4 | cliffhanger | 55.8 | 67.0 | Cliffhanger (exit line) · scene_1 |

#### #20 · Episode 5 · `00:00.000` → `00:15.800` (15.8s)

global=**7.542** · ep_score=6.57 · role=*acquisition* · tags=['conflict'] · spine=['identity_lineage', 'wedding_betrayal', 'power_disownment']

| Field | Value |
|-------|-------|
| **Hook** | You will not leave this church carrying the Ashcroft name. |
| **Cliffhanger** | "The vows are spoken, Father. I am his wife now." |
| **Why it works** | Conflict beat (6.57/10): identity/lineage stakes land fast; betrayal/power turn is instantly readable cold. |
| **Why post here** | Ep 5 · acquisition: cold-open fuel — works without binge homework. Continuity fit 9.79/10, clarity 7.6/10, spine=[identity_lineage, wedding_betrayal, power_disownment], tags=[conflict] (tags not scored), global=7.542. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 0.0 | 15.8 | Master in–out (cut this whole promo) |
| 2 | hook | 0.0 | 6.0 | Hook (opening lines) · scene_1 |
| 3 | rise | 6.0 | 10.5 | Escalation · scene_1 |
| 4 | cliffhanger | 10.5 | 15.8 | Cliffhanger (exit line) · scene_1 |

#### #21 · Episode 31 · `00:21.000` → `00:59.000` (38.0s)

global=**7.901** · ep_score=7.22 · role=*climax* · tags=['cliffhanger'] · spine=['identity_lineage', 'violence_peril', 'rival_court']

| Field | Value |
|-------|-------|
| **Hook** | Everyone saw you. Everyone watched him chose Clarisse. |
| **Cliffhanger** | "And everyone watched you walk away alone." |
| **Why it works** | Cliffhanger beat (7.22/10): betrayal/power turn is instantly readable cold. |
| **Why post here** | Ep 31 · climax: peak tension for invested viewers. Continuity fit 9.43/10, clarity 6.4/10, spine=[identity_lineage, violence_peril, rival_court], tags=[cliffhanger] (tags not scored), global=7.901. |

**Segments (in order):**

| # | Role | Start (s) | End (s) | Label |
|--:|------|----------:|--------:|-------|
| 1 | full_window | 21.0 | 59.0 | Master in–out (cut this whole promo) |
| 2 | hook | 21.0 | 34.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 34.8 | 54.8 | Escalation · scene_1 |
| 4 | cliffhanger | 54.8 | 59.0 | Cliffhanger (exit line) · scene_1 |

---

## B. Best promo per episode (catalogue)

### Episode 1

*Logline:* Lady Juliana arrives at the cathedral in her late mother's bridal gown, only to suffer the ultimate betrayal when her fiancé Gerald abandons her at the altar for her cruel sister Clarissa with her family's full blessing.

**Cut:** `01:42.500` → `02:18.000` (35.5s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional']

- **Hook:** "She has beauty, connections, and a future worth protecting."
- **Cliffhanger:** "...when Clarissa is the true jewel of the county."
- **Why it works:** Emotional beat (7.2/10): identity/lineage stakes land fast; betrayal/power turn is instantly readable cold.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 102.5 | 138.0 | Master in–out (cut this whole promo) |
| 2 | hook | 102.5 | 113.0 | Hook (opening lines) · scene_1 |
| 3 | rise | 113.0 | 128.5 | Escalation · scene_1 |
| 4 | cliffhanger | 128.5 | 138.0 | Cliffhanger (exit line) · scene_1 |

### Episode 2

*Logline:* Publicly cast aside at the altar by Gerald for her sister Clarissa and abandoned by her own family, Juliana stands tall and turns her public humiliation into an unyielding indictment of Gerald's honor.

**Cut:** `00:00.000` → `00:20.700` (20.7s) | **In campaign pack:** yes (#7) | **ep_score:** 7.42/10 | **types:** ['emotional']

- **Hook:** "I cannot marry you, Juliana."
- **Cliffhanger:** "You gave me your word before both our families."
- **Why it works:** Emotional beat (7.42/10): betrayal/power turn is instantly readable cold.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 0.0 | 20.7 | Master in–out (cut this whole promo) |
| 2 | hook | 0.0 | 6.6 | Hook (opening lines) · scene_1 |
| 3 | rise | 6.6 | 12.0 | Escalation · scene_1 |
| 4 | cliffhanger | 12.0 | 20.7 | Cliffhanger (exit line) · scene_1 |

### Episode 3

*Logline:* Banished from her mother's chapel and seized by guards at her family's command, Juliana is rescued by an imposing, scarred stranger who intervenes with lethal grace—and drops to one knee with a proposal that shocks high society.

**Cut:** `01:48.800` → `02:25.750` (37.0s) | **In campaign pack:** yes (#1) | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger', 'romantic']

- **Hook:** "...to remember your worth."
- **Cliffhanger:** "Lady Juliana... accept my hand."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 108.8 | 145.75 | Master in–out (cut this whole promo) |
| 2 | hook | 108.8 | 117.9 | Hook (opening lines) · scene_3 |
| 3 | rise | 117.9 | 129.9 | Escalation · scene_3 |
| 4 | cliffhanger | 129.9 | 145.75 | Cliffhanger (exit line) · scene_3 |

### Episode 4

*Logline:* Defying Gerald and Clarissa's cruel mockery, Juliana accepts the mysterious scarred warrior's solemn proposal and is officially wed, choosing exile and dignity over her family's cruelty as they walk out into the light together.

**Cut:** `01:54.000` → `02:29.000` (35.0s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'thrilling']

- **Hook:** "...husband and wife!"
- **Cliffhanger:** "Come, Lady Juliana."
- **Why it works:** Emotional/Thrilling beat (7.2/10): betrayal/power turn is instantly readable cold; physical peril raises binge urgency.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 114.0 | 149.0 | Master in–out (cut this whole promo) |
| 2 | hook | 114.0 | 122.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 122.8 | 136.0 | Escalation · scene_1 |
| 4 | cliffhanger | 136.0 | 149.0 | Cliffhanger (exit line) · scene_1 |

### Episode 5

*Logline:* Formally disowned and stripped of her inheritance, Juliana is publicly humiliated when her stepmother throws her late mother's treasured ledger into the mud, but her rugged new husband defends her dignity and guides her away from her callous family.

**Cut:** `01:06.500` → `01:41.500` (35.0s) | **In campaign pack:** yes (#15) | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic']

- **Hook:** "Here you go."
- **Cliffhanger:** "Choose your next words carefully."
- **Why it works:** Emotional/Romantic beat (7.2/10): identity/lineage stakes land fast.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 66.5 | 101.5 | Master in–out (cut this whole promo) |
| 2 | hook | 66.5 | 80.0 | Hook (opening lines) · scene_1 |
| 3 | rise | 80.0 | 89.0 | Escalation · scene_1 |
| 4 | cliffhanger | 89.0 | 101.5 | Cliffhanger (exit line) · scene_1 |

### Episode 6

*Logline:* Seeking shelter from the cold rain, Juliana arrives at her new husband's modest woodland cottage and discovers an unexpected sense of peace beside the hearth.

**Cut:** `00:33.700` → `01:04.100` (30.4s) | **In campaign pack:** no | **ep_score:** 6.96/10 | **types:** ['emotional']

- **Hook:** "I am sorry."
- **Cliffhanger:** "But not because of you."
- **Why it works:** Emotional beat (6.96/10): betrayal/power turn is instantly readable cold.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 33.7 | 64.1 | Master in–out (cut this whole promo) |
| 2 | hook | 33.7 | 33.7 | Hook · scene_1 |
| 3 | cliffhanger | 33.7 | 64.1 | Cliffhanger · scene_2 |

### Episode 7

*Logline:* When Gerald and his spiteful companion arrive at the woodland cottage to mock Juliana's fallen status, her stoic new husband returns from the forest to silently send them fleeing.

**Cut:** `01:21.000` → `01:56.000` (35.0s) | **In campaign pack:** no | **ep_score:** 6.96/10 | **types:** ['emotional']

- **Hook:** "Gerald, don't let him frighten you."
- **Cliffhanger:** "I didn't need to."
- **Why it works:** Emotional beat (6.96/10): clean hook→pressure→turn inside a tight window.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 81.0 | 116.0 | Master in–out (cut this whole promo) |
| 2 | hook | 81.0 | 90.0 | Hook (opening lines) · scene_3 |
| 3 | rise | 90.0 | 96.0 | Escalation · scene_3 |
| 4 | cliffhanger | 96.0 | 116.0 | Cliffhanger (exit line) · scene_3 |

### Episode 8

*Logline:* As Juliana inspects her late mother's weathered herbal grimoire, Alexander bonds with her over rustic medicinal knowledge and war-worn memories, gently altering her perception of what true wealth means.

**Cut:** `00:00.000` → `00:28.100` (28.1s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic', 'thrilling']

- **Hook:** "Some of the pages are ruined. Careful."
- **Cliffhanger:** "Your hair and beard..."
- **Why it works:** Emotional/Romantic beat (7.2/10): identity/lineage stakes land fast; physical peril raises binge urgency.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 0.0 | 28.1 | Master in–out (cut this whole promo) |
| 2 | hook | 0.0 | 10.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 10.5 | 19.3 | Escalation · scene_1 |
| 4 | cliffhanger | 19.3 | 28.1 | Cliffhanger (exit line) · scene_1 |

### Episode 9

*Logline:* When a frantic mother brings her critically ill child to the woodland cottage, Juliana successfully cures him with her mother's herbal remedies, unknowingly igniting dangerous rumors that reach the ears of the Blond Nobleman.

**Cut:** `00:38.200` → `01:14.800` (36.6s) | **In campaign pack:** yes (#8) | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger']

- **Hook:** "Alexander, I need hot water."
- **Cliffhanger:** "I will tell the village what you did. They will never forget you."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 38.2 | 74.8 | Master in–out (cut this whole promo) |
| 2 | hook | 38.2 | 48.2 | Hook (opening lines) · scene_1 |
| 3 | rise | 48.2 | 64.0 | Escalation · scene_1 |
| 4 | cliffhanger | 64.0 | 74.8 | Cliffhanger (exit line) · scene_1 |

### Episode 10

*Logline:* When Alexander returns to the cottage gravely wounded and soaked in blood, Juliana tends to his injuries, leading to an intimate confrontation where their unspoken feelings and scarred pasts finally collide.

**Cut:** `00:47.300` → `01:22.500` (35.2s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'thrilling']

- **Hook:** "It is over."
- **Cliffhanger:** "Perhaps it is your hand."
- **Why it works:** Emotional/Thrilling beat (7.2/10): physical peril raises binge urgency.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 47.3 | 82.5 | Master in–out (cut this whole promo) |
| 2 | hook | 47.3 | 55.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 55.5 | 68.8 | Escalation · scene_1 |
| 4 | cliffhanger | 68.8 | 82.5 | Cliffhanger (exit line) · scene_1 |

### Episode 11

*Logline:* Gerald and Clarissa arrive at the cottage with an armed constable accusing Alexander of grand theft, culminating in a devastating planted discovery that threatens to tear the newlyweds apart.

**Cut:** `00:18.500` → `00:53.600` (35.1s) | **In campaign pack:** yes (#5) | **ep_score:** 7.42/10 | **types:** ['cliffhanger', 'revelation']

- **Hook:** "Your husband stole my gold pocket watch!"
- **Cliffhanger:** "Let them."
- **Why it works:** Cliffhanger/Revelation beat (7.42/10): high-voltage delivery.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 18.5 | 53.6 | Master in–out (cut this whole promo) |
| 2 | hook | 18.5 | 28.9 | Hook (opening lines) · scene_1 |
| 3 | rise | 28.9 | 41.1 | Escalation · scene_1 |
| 4 | cliffhanger | 41.1 | 53.6 | Cliffhanger (exit line) · scene_1 |

### Episode 12

*Logline:* When the Constable attempts to arrest Alexander for grand theft, Clarissa offers Juliana a sadistic ultimatum: retrieve a signet ring from frozen, razor-sharp blackthorn briars with her bare hands, or watch her husband hang.

**Cut:** `00:14.300` → `00:52.300` (38.0s) | **In campaign pack:** no | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger', 'romantic']

- **Hook:** "The proof is in his coat, Juliana. A valuable pocket watch doesn't just walk into a beggar's pocket."
- **Cliffhanger:** "My emerald signet ring fell deep into the frozen blackthorn briars at Ashworth Manor. The thorns have grown over it..."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 14.3 | 52.3 | Master in–out (cut this whole promo) |
| 2 | hook | 14.3 | 27.9 | Hook (opening lines) · scene_1 |
| 3 | rise | 27.9 | 40.0 | Escalation · scene_1 |
| 4 | cliffhanger | 40.0 | 52.3 | Cliffhanger (exit line) · scene_1 |

### Episode 13

*Logline:* Defying Alexander's desperate pleas, Juliana crawls barehanded into the razor-sharp blackthorn garden, enduring brutal lacerations under Clarissa and Gerald's cruel taunts until she unearths the lost emerald signet ring.

**Cut:** `01:18.500` → `01:54.000` (35.5s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'thrilling']

- **Hook:** "Ah!"
- **Cliffhanger:** "Please, ring... you have to be here."
- **Why it works:** Emotional/Thrilling beat (7.2/10): physical peril raises binge urgency; high-voltage delivery.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 78.5 | 114.0 | Master in–out (cut this whole promo) |
| 2 | hook | 78.5 | 85.8 | Hook (opening lines) · scene_2 |
| 3 | rise | 85.8 | 102.5 | Escalation · scene_2 |
| 4 | cliffhanger | 102.5 | 114.0 | Cliffhanger (exit line) · scene_2 |

### Episode 14

*Logline:* After Juliana secures Alexander's freedom with the unearthed emerald signet ring, he carries her home to bandage her torn hands, silently swearing that no one will ever harm her again.

**Cut:** `00:01.000` → `00:38.500` (37.5s) | **In campaign pack:** yes (#13) | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger', 'romantic', 'thrilling']

- **Hook:** "I found it."
- **Cliffhanger:** "You should never have had to bleed for me."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): betrayal/power turn is instantly readable cold; intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 1.0 | 38.5 | Master in–out (cut this whole promo) |
| 2 | hook | 1.0 | 13.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 13.5 | 25.5 | Escalation · scene_1 |
| 4 | cliffhanger | 25.5 | 38.5 | Cliffhanger (exit line) · scene_1 |

### Episode 15

*Logline:* When ruthless thugs desecrate Juliana's medicinal garden and trample her late mother's herbs, a protective Alexander charges into the night to defend her.

**Cut:** `00:08.500` → `00:46.400` (37.9s) | **In campaign pack:** yes (#18) | **ep_score:** 7.39/10 | **types:** ['emotional', 'revelation', 'romantic', 'thrilling']

- **Hook:** "Stop! What are you doing?!"
- **Cliffhanger:** "Get out of the way!"
- **Why it works:** Emotional/Revelation beat (7.39/10): identity/lineage stakes land fast; physical peril raises binge urgency.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 8.5 | 46.4 | Master in–out (cut this whole promo) |
| 2 | hook | 8.5 | 22.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 22.5 | 34.0 | Escalation · scene_1 |
| 4 | cliffhanger | 34.0 | 46.4 | Cliffhanger (exit line) · scene_1 |

### Episode 16

*Logline:* When hired thugs attack Juliana's medicinal garden, Alexander unleashes his combat training to effortlessly overpower them, extracting a shocking confession that unmasks Gerald Harrington as the mastermind.

**Cut:** `00:48.000` → `01:23.190` (35.2s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'thrilling']

- **Hook:** "Who?!"
- **Cliffhanger:** "No."
- **Why it works:** Emotional/Thrilling beat (7.2/10): identity/lineage stakes land fast; betrayal/power turn is instantly readable cold.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 48.0 | 83.19 | Master in–out (cut this whole promo) |
| 2 | hook | 48.0 | 59.0 | Hook (opening lines) · scene_1 |
| 3 | rise | 59.0 | 70.2 | Escalation · scene_1 |
| 4 | cliffhanger | 70.2 | 83.19 | Cliffhanger (exit line) · scene_1 |

### Episode 17

*Logline:* In the aftermath of the brutal attack, Alexander repairs Juliana's devastated garden and swears to protect her with his life, drawing them into a tender, intimate embrace by the hearth.

**Cut:** `00:39.000` → `01:23.500` (44.5s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic', 'thrilling']

- **Hook:** "You were bleeding last night."
- **Cliffhanger:** "So is yours."
- **Why it works:** Emotional/Romantic beat (7.2/10): physical peril raises binge urgency.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 39.0 | 83.5 | Master in–out (cut this whole promo) |
| 2 | hook | 39.0 | 39.0 | Hook · scene_1 |
| 3 | cliffhanger | 39.0 | 83.5 | Cliffhanger · scene_2 |

### Episode 18

*Logline:* When their cottage is deliberately set ablaze in the dead of night, Alexander risks his life to rescue Juliana and her mother's cherished ledger from the inferno, vowing relentless vengeance against those responsible.

**Cut:** `00:00.000` → `00:28.900` (28.9s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic']

- **Hook:** "Alexander!"
- **Cliffhanger:** "Fire."
- **Why it works:** Emotional/Romantic beat (7.2/10): intimacy and danger collide; high-voltage delivery.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 0.0 | 28.9 | Master in–out (cut this whole promo) |
| 2 | hook | 0.0 | 28.9 | Hook · scene_1 |
| 3 | cliffhanger | 28.9 | 28.9 | Cliffhanger · scene_2 |

### Episode 19

*Logline:* Standing before the smoldering ash of their home, Juliana and Alexander receive shelter and food from grateful villagers before Alexander meets in secret with a loyal spy, learning that his usurping enemies have imprisoned his mother and claimed his ducal seat.

**Cut:** `00:49.500` → `01:28.900` (39.4s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional']

- **Hook:** "Lord Sterling's influence has grown since your disappearance. He has men in the county offices, the courts, even among the household staff."
- **Cliffhanger:** "Then Ashburg will remember who it belongs to."
- **Why it works:** Emotional beat (7.2/10): identity/lineage stakes land fast.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 49.5 | 88.9 | Master in–out (cut this whole promo) |
| 2 | hook | 49.5 | 70.6 | Hook (opening lines) · scene_2 |
| 3 | rise | 70.6 | 78.8 | Escalation · scene_2 |
| 4 | cliffhanger | 78.8 | 88.9 | Cliffhanger (exit line) · scene_2 |

### Episode 20

*Logline:* Inside the opulent Ashbury estate, the treacherous Rupert and Catherine plot to seize the ducal title as the Dowager Duchess slowly withers, while in an icy barn, Juliana defiantly prepares remedies to save the fever-stricken villagers.

**Cut:** `01:28.200` → `01:54.750` (26.5s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic']

- **Hook:** "Let the peasants rot in their barns."
- **Cliffhanger:** "This house will only bow to me."
- **Why it works:** Emotional/Romantic beat (7.2/10): intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 88.2 | 114.75 | Master in–out (cut this whole promo) |
| 2 | hook | 88.2 | 88.2 | Hook · scene_3 |
| 3 | cliffhanger | 88.2 | 114.75 | Cliffhanger · scene_4 |

### Episode 21

*Logline:* After defying her own despair to cure a fever-stricken village boy with her mother's herbal remedies, Lady Juliana learns that the Dowager Duchess is secretly withering away from a mysterious illness inside Ashbury Manor.

**Cut:** `01:16.000` → `01:54.000` (38.0s) | **In campaign pack:** yes (#9) | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger']

- **Hook:** "Keep him warm. Give him three drops of this coltsfoot tea every morning."
- **Cliffhanger:** "Inside that massive house with all their wealth, she is fading to nothing, and no one can stop it."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 76.0 | 114.0 | Master in–out (cut this whole promo) |
| 2 | hook | 76.0 | 90.8 | Hook (opening lines) · scene_3 |
| 3 | rise | 90.8 | 99.2 | Escalation · scene_3 |
| 4 | cliffhanger | 99.2 | 114.0 | Cliffhanger (exit line) · scene_3 |

### Episode 22

*Logline:* Disguised as a common scullery maid, Lady Juliana infiltrates Ashbury Manor alongside Prudence and slips into the forbidden West Wing, where she discovers the dying Dowager Duchess suffering from an unnatural, poisoned affliction.

**Cut:** `01:42.000` → `02:11.000` (29.0s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional']

- **Hook:** "Your Grace?"
- **Cliffhanger:** "Who has been treating you?"
- **Why it works:** Emotional beat (7.2/10): identity/lineage stakes land fast; open question pulls the next click.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 102.0 | 131.0 | Master in–out (cut this whole promo) |
| 2 | hook | 102.0 | 102.0 | Hook · scene_3 |
| 3 | cliffhanger | 102.0 | 131.0 | Cliffhanger · scene_4 |

### Episode 23

*Logline:* After examining the dying Dowager Duchess's blackened fingernails and consulting her late mother's remedy journal, Lady Juliana discovers the Duchess is being poisoned with arsenic—only for someone to arrive at the bedroom door just as she begins concocting the antidote.

**Cut:** `00:48.000` → `01:24.500` (36.5s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional']

- **Hook:** "Mother."
- **Cliffhanger:** "Poison?"
- **Why it works:** Emotional beat (7.2/10): identity/lineage stakes land fast; open question pulls the next click.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 48.0 | 84.5 | Master in–out (cut this whole promo) |
| 2 | hook | 48.0 | 62.0 | Hook (opening lines) · scene_1 |
| 3 | rise | 62.0 | 76.0 | Escalation · scene_1 |
| 4 | cliffhanger | 76.0 | 84.5 | Cliffhanger (exit line) · scene_1 |

### Episode 24

*Logline:* When an arrogant noblewoman catches Juliana in the poisoned Dowager Duchess's chambers, she strikes Juliana with a riding crop and sentences her to scrub the hearth, unaware that Juliana has secretly hidden the antidote and remedy journal to finish the Duchess's cure.

**Cut:** `00:13.000` → `00:48.000` (35.0s) | **In campaign pack:** no | **ep_score:** 7.39/10 | **types:** ['emotional', 'revelation', 'romantic']

- **Hook:** "And who gave you permission to enter this chamber?"
- **Cliffhanger:** "Good. Perhaps we can teach you your place."
- **Why it works:** Emotional/Revelation beat (7.39/10): intimacy and danger collide; open question pulls the next click.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 13.0 | 48.0 | Master in–out (cut this whole promo) |
| 2 | hook | 13.0 | 26.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 26.5 | 36.5 | Escalation · scene_1 |
| 4 | cliffhanger | 36.5 | 48.0 | Cliffhanger (exit line) · scene_1 |

### Episode 25

*Logline:* Deep in the misty forest, Alexander confronts an injured Juliana and uncovers the wound inflicted by Lady Catherine, reacting with fury and protective concern upon learning that someone is systematically poisoning the Dowager Duchess with arsenic.

**Cut:** `02:08.200` → `02:48.000` (39.8s) | **In campaign pack:** no | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger', 'thrilling']

- **Hook:** "Because you were standing inside a house where someone is poisoning a woman... and you never told me."
- **Cliffhanger:** "Everything you saw."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast; physical peril raises binge urgency.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 128.2 | 168.0 | Master in–out (cut this whole promo) |
| 2 | hook | 128.2 | 142.4 | Hook (opening lines) · scene_1 |
| 3 | rise | 142.4 | 151.2 | Escalation · scene_1 |
| 4 | cliffhanger | 151.2 | 168.0 | Cliffhanger (exit line) · scene_1 |

### Episode 26

*Logline:* While secretly administering a charcoal antidote to the poisoned Dowager Duchess in the dead of night, Juliana is stunned when the Duchess suddenly recognizes a distinctive family ring on her hand and fiercely demands the truth about her identity.

**Cut:** `00:30.800` → `01:07.000` (36.2s) | **In campaign pack:** yes (#19) | **ep_score:** 7.6/10 | **types:** ['emotional', 'revelation']

- **Hook:** "You... you are no common servant. You took Catherine's whip for me the other day."
- **Cliffhanger:** "Yes. But the charcoal is fighting the poison. You are safe now."
- **Why it works:** Emotional/Revelation beat (7.6/10): identity/lineage stakes land fast.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 30.8 | 67.0 | Master in–out (cut this whole promo) |
| 2 | hook | 30.8 | 39.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 39.8 | 55.8 | Escalation · scene_1 |
| 4 | cliffhanger | 55.8 | 67.0 | Cliffhanger (exit line) · scene_1 |

### Episode 27

*Logline:* The Dowager Duchess realizes Juliana's wedding ring bears the Ashbourne crest belonging to her lost son, but before Juliana can reveal Alexander's name, Rupert and Catherine storm the bedchamber and frame her for poisoning the Duchess.

**Cut:** `00:06.400` → `00:44.200` (37.8s) | **In campaign pack:** no | **ep_score:** 7.22/10 | **types:** ['cliffhanger']

- **Hook:** "My husband. He gave it to me when we wed."
- **Cliffhanger:** "He never spoke of his officers. He only spoke of survival."
- **Why it works:** Cliffhanger beat (7.22/10): identity/lineage stakes land fast.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 6.4 | 44.2 | Master in–out (cut this whole promo) |
| 2 | hook | 6.4 | 16.4 | Hook (opening lines) · scene_1 |
| 3 | rise | 16.4 | 34.9 | Escalation · scene_1 |
| 4 | cliffhanger | 34.9 | 44.2 | Cliffhanger (exit line) · scene_1 |

### Episode 28

*Logline:* Rupert and Catherine frame Juliana for poisoning the Duchess despite the bedridden matriarch's protests, uncovering Juliana's true noble identity and her mother's herbarium before ordering her to the castle dungeons.

**Cut:** `00:15.200` → `01:01.300` (46.1s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic']

- **Hook:** "I did not poison her! Look at her eyes, the fever has broken!"
- **Cliffhanger:** "You are merely confused."
- **Why it works:** Emotional/Romantic beat (7.2/10): identity/lineage stakes land fast; intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 15.2 | 61.3 | Master in–out (cut this whole promo) |
| 2 | hook | 15.2 | 32.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 32.8 | 47.0 | Escalation · scene_1 |
| 4 | cliffhanger | 47.0 | 61.3 | Cliffhanger (exit line) · scene_1 |

### Episode 29

*Logline:* Thrown into the castle's subterranean wet cells as Catherine threatens to burn her mother's herbarium and frame her for witchcraft, Juliana breaks down in isolation before swearing that they will never take Alexander from her.

**Cut:** `00:00.000` → `00:20.100` (20.1s) | **In campaign pack:** no | **ep_score:** 6.89/10 | **types:** ['emotional']

- **Hook:** "Catherine! Please! That book is my mother's only legacy!"
- **Cliffhanger:** "It contains years of her work! Her knowledge! Everything she left me!"
- **Why it works:** Emotional beat (6.89/10): identity/lineage stakes land fast; high-voltage delivery.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 0.0 | 20.1 | Master in–out (cut this whole promo) |
| 2 | hook | 0.0 | 20.1 | Hook · scene_1 |
| 3 | cliffhanger | 20.1 | 20.1 | Cliffhanger · scene_2 |

### Episode 30

*Logline:* When rumors of the poisoned Duchess begin spreading among the servants, Rupert and Catherine conspire with an elder nobleman to fabricate a witchcraft charge against Juliana, sealing her fate for the gallows.

**Cut:** `00:08.800` → `00:47.300` (38.5s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic']

- **Hook:** "You have a rat in your cellar, Rupert. And the servants are beginning to smell it."
- **Cliffhanger:** "We stop hiding the prisoner."
- **Why it works:** Emotional/Romantic beat (7.2/10): identity/lineage stakes land fast; intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 8.8 | 47.3 | Master in–out (cut this whole promo) |
| 2 | hook | 8.8 | 25.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 25.8 | 39.8 | Escalation · scene_1 |
| 4 | cliffhanger | 39.8 | 47.3 | Cliffhanger (exit line) · scene_1 |

### Episode 31

*Logline:* Catherine enters the wet cells armed with a red-hot iron and Juliana's late mother's botanical book, subjecting the chained heiress to ruthless psychological torment until Juliana's unyielding pride pushes Catherine to a violent brink.

**Cut:** `01:58.400` → `02:40.000` (41.6s) | **In campaign pack:** yes (#21) | **ep_score:** 7.39/10 | **types:** ['emotional', 'revelation']

- **Hook:** "Then why are you so desperate to make me kneel?"
- **Cliffhanger:** "One flame, and your mother's life's work becomes ash."
- **Why it works:** Emotional/Revelation beat (7.39/10): identity/lineage stakes land fast; open question pulls the next click.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 118.4 | 160.0 | Master in–out (cut this whole promo) |
| 2 | hook | 118.4 | 132.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 132.8 | 143.8 | Escalation · scene_1 |
| 4 | cliffhanger | 143.8 | 160.0 | Cliffhanger (exit line) · scene_1 |

### Episode 32

*Logline:* Cornered and chained in the damp dungeon, Juliana shatters Catherine's cruelty with unshakeable dignity and the truth about love and worth, driving Catherine into a murderous fury.

**Cut:** `01:47.200` → `02:22.400` (35.2s) | **In campaign pack:** yes (#2) | **ep_score:** 8.05/10 | **types:** ['emotional', 'cliffhanger', 'revelation', 'romantic']

- **Hook:** "And a woman who never embarrasses the people standing behind her."
- **Cliffhanger:** "...but you will never have the courage to earn what you demand from everyone else."
- **Why it works:** Emotional/Cliffhanger beat (8.05/10): identity/lineage stakes land fast; intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 107.2 | 142.4 | Master in–out (cut this whole promo) |
| 2 | hook | 107.2 | 119.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 119.5 | 131.8 | Escalation · scene_1 |
| 4 | cliffhanger | 131.8 | 142.4 | Cliffhanger (exit line) · scene_1 |

### Episode 33

*Logline:* Under cruel coercion and threats to send her seven-year-old brother to the county gaol, a young maid is manipulated into giving false testimony framing Juliana for witchcraft.

**Cut:** `02:18.000` → `02:54.040` (36.0s) | **In campaign pack:** yes (#17) | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger']

- **Hook:** "Before the magistrate."
- **Cliffhanger:** "Save your tears for the trial."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): clean hook→pressure→turn inside a tight window.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 138.0 | 174.04 | Master in–out (cut this whole promo) |
| 2 | hook | 138.0 | 146.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 146.5 | 159.5 | Escalation · scene_1 |
| 4 | cliffhanger | 159.5 | 174.04 | Cliffhanger (exit line) · scene_1 |

### Episode 34

*Logline:* Put on trial for witchcraft and poisoning, Lady Juliana stands proud and defiant in the prisoner's dock, refusing to renounce her mother's herbal medicine even after her coerced maid gives false testimony against her.

**Cut:** `02:22.200` → `03:04.500` (42.3s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional']

- **Hook:** "Lady Juliana, if you wish to save yourself, renounce these practices."
- **Cliffhanger:** "Lady Juliana Ashcroft..."
- **Why it works:** Emotional beat (7.2/10): identity/lineage stakes land fast.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 142.2 | 184.5 | Master in–out (cut this whole promo) |
| 2 | hook | 142.2 | 156.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 156.8 | 173.6 | Escalation · scene_1 |
| 4 | cliffhanger | 173.6 | 184.5 | Cliffhanger (exit line) · scene_1 |

### Episode 35

*Logline:* Fleeing her captivity through a secret passage, Alexander's elderly mother treks through a bitter blizzard to a secluded cabin, where she tearfully reunites with her presumed-dead son and learns the horrifying conspiracy behind his supposed demise.

**Cut:** `01:11.500` → `02:05.500` (54.0s) | **In campaign pack:** yes (#3) | **ep_score:** 8.05/10 | **types:** ['emotional', 'cliffhanger', 'revelation']

- **Hook:** "Then how did you survive?"
- **Cliffhanger:** "Then why did they never tell us?"
- **Why it works:** Emotional/Cliffhanger beat (8.05/10): identity/lineage stakes land fast; open question pulls the next click.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 71.5 | 125.5 | Master in–out (cut this whole promo) |
| 2 | hook | 71.5 | 92.0 | Hook (opening lines) · scene_3 |
| 3 | rise | 92.0 | 106.0 | Escalation · scene_3 |
| 4 | cliffhanger | 106.0 | 125.5 | Cliffhanger (exit line) · scene_3 |

### Episode 36

*Logline:* Learning from his mother that Rupert and Catherine framed Juliana for witchcraft and sentenced her to death right after their upcoming wedding, Alexander vows to return from the dead and reclaim everything stolen from him.

**Cut:** `00:41.600` → `01:18.100` (36.5s) | **In campaign pack:** yes (#10) | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger']

- **Hook:** "They declared me dead."
- **Cliffhanger:** "She went into Ashbourne Manor to save you. She never came back."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 41.6 | 78.1 | Master in–out (cut this whole promo) |
| 2 | hook | 41.6 | 51.8 | Hook (opening lines) · scene_1 |
| 3 | rise | 51.8 | 63.8 | Escalation · scene_1 |
| 4 | cliffhanger | 63.8 | 78.1 | Cliffhanger (exit line) · scene_1 |

### Episode 37

*Logline:* As Rupert and Catherine issue wedding invitations paired with Juliana's public execution decree to terrorize the county, Juliana endures starvation in the dungeon, refusing to break her spirit.

**Cut:** `00:50.000` → `01:27.500` (37.5s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic']

- **Hook:** "Lady Catherine Ashbridge."
- **Cliffhanger:** "Juliana's ruin will be a lesson. And we will be there to watch."
- **Why it works:** Emotional/Romantic beat (7.2/10): identity/lineage stakes land fast; betrayal/power turn is instantly readable cold.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 50.0 | 87.5 | Master in–out (cut this whole promo) |
| 2 | hook | 50.0 | 58.5 | Hook (opening lines) · scene_2 |
| 3 | rise | 58.5 | 72.5 | Escalation · scene_2 |
| 4 | cliffhanger | 72.5 | 87.5 | Cliffhanger (exit line) · scene_2 |

### Episode 38

*Logline:* A compassionate guard secretly feeds Juliana bread in the dungeon, strengthening her resolve to protect Alexander's secrets just as distant wedding bells signal the start of Rupert's nuptials and her impending execution.

**Cut:** `00:23.500` → `01:00.500` (37.0s) | **In campaign pack:** no | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger']

- **Hook:** "Thank you."
- **Cliffhanger:** "And if I have only one thing left to give..."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): clean hook→pressure→turn inside a tight window.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 23.5 | 60.5 | Master in–out (cut this whole promo) |
| 2 | hook | 23.5 | 36.5 | Hook (opening lines) · scene_1 |
| 3 | rise | 36.5 | 50.5 | Escalation · scene_1 |
| 4 | cliffhanger | 50.5 | 60.5 | Cliffhanger (exit line) · scene_1 |

### Episode 39

*Logline:* While Alexander's loyal men infiltrate and neutralize the royal guards stationed outside the cathedral, Alexander sheds his rugged disguise, dons his ducal regalia, and marches forth to reclaim his house and rescue Juliana.

**Cut:** `01:08.500` → `01:38.410` (29.9s) | **In campaign pack:** no | **ep_score:** 6.97/10 | **types:** ['emotional']

- **Hook:** "Your Grace."
- **Cliffhanger:** "And I am bringing my wife home."
- **Why it works:** Emotional beat (6.97/10): clean hook→pressure→turn inside a tight window.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 68.5 | 98.41 | Master in–out (cut this whole promo) |
| 2 | hook | 68.5 | 68.5 | Hook · scene_4 |
| 3 | cliffhanger | 68.5 | 98.41 | Cliffhanger · scene_5 |

### Episode 40

*Logline:* High society gathers at the grand cathedral for Rupert and Catherine's lavish wedding, while the conspirators ensure every exit is sealed to seal Juliana's execution—unaware that Alexander's retribution is already at their gates.

**Cut:** `01:18.500` → `01:50.080` (31.6s) | **In campaign pack:** no | **ep_score:** 6.97/10 | **types:** ['emotional', 'romantic']

- **Hook:** "She looks like a queen."
- **Cliffhanger:** "And you look better in silk than you ever did as an ignored cousin."
- **Why it works:** Emotional/Romantic beat (6.97/10): betrayal/power turn is instantly readable cold; intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 78.5 | 110.08 | Master in–out (cut this whole promo) |
| 2 | hook | 78.5 | 78.5 | Hook · scene_3 |
| 3 | cliffhanger | 78.5 | 110.08 | Cliffhanger · scene_4 |

### Episode 41

*Logline:* At the height of Catherine and Rupert's lavish wedding, Juliana is paraded before high society in chains to be publicly disgraced—until a deafening explosion shatters the cathedral entrance, heralding Alexander's vengeful assault.

**Cut:** `00:48.600` → `01:24.500` (35.9s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic']

- **Hook:** "And now they can all see what you truly are."
- **Cliffhanger:** "Shall we?"
- **Why it works:** Emotional/Romantic beat (7.2/10): identity/lineage stakes land fast; betrayal/power turn is instantly readable cold.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 48.6 | 84.5 | Master in–out (cut this whole promo) |
| 2 | hook | 48.6 | 64.0 | Hook (opening lines) · scene_1 |
| 3 | rise | 64.0 | 77.5 | Escalation · scene_1 |
| 4 | cliffhanger | 77.5 | 84.5 | Cliffhanger (exit line) · scene_1 |

### Episode 42

*Logline:* Emerging from the smoke of the shattered cathedral gates in full ducal regalia, Alexander confronts Rupert, wins the loyalty of the royal guards, and is proclaimed the rightful Duke of Ashburn by his weeping mother.

**Cut:** `00:12.800` → `01:17.500` (64.7s) | **In campaign pack:** no | **ep_score:** 7.02/10 | **types:** ['emotional', 'romantic']

- **Hook:** "You already know."
- **Cliffhanger:** "And now, Rupert... we settle what you stole." --- SCRIPT END ---
- **Why it works:** Emotional/Romantic beat (7.02/10): identity/lineage stakes land fast; betrayal/power turn is instantly readable cold.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 12.8 | 77.5 | Master in–out (cut this whole promo) |
| 2 | hook | 12.8 | 25.2 | Hook (opening lines) · scene_1 |
| 3 | rise | 25.2 | 42.5 | Escalation · scene_1 |
| 4 | cliffhanger | 42.5 | 77.5 | Cliffhanger (exit line) · scene_1 |

### Episode 43

*Logline:* When Rupert frantically orders Alexander's arrest, the royal guards refuse and salute the true Duke, before damning Crown intelligence documents expose Rupert and Lord Sterling's treasonous plot.

**Cut:** `01:06.500` → `01:54.960` (48.5s) | **In campaign pack:** no | **ep_score:** 7.2/10 | **types:** ['emotional', 'romantic']

- **Hook:** "My God..."
- **Cliffhanger:** "Going somewhere, Lord Sterling?"
- **Why it works:** Emotional/Romantic beat (7.2/10): identity/lineage stakes land fast; betrayal/power turn is instantly readable cold.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 66.5 | 114.96 | Master in–out (cut this whole promo) |
| 2 | hook | 66.5 | 77.6 | Hook (opening lines) · scene_1 |
| 3 | rise | 77.6 | 99.8 | Escalation · scene_1 |
| 4 | cliffhanger | 99.8 | 114.96 | Cliffhanger (exit line) · scene_1 |

### Episode 44

*Logline:* As Lord Sterling and Rupert are apprehended by the Crown, Catherine pleads with Alexander for their past love, only to be coldly rejected as he walks toward his chained bride, Juliana.

**Cut:** `00:28.400` → `01:05.000` (36.6s) | **In campaign pack:** yes (#4) | **ep_score:** 8.05/10 | **types:** ['emotional', 'cliffhanger', 'revelation', 'romantic']

- **Hook:** "Do you know what this did to me?"
- **Cliffhanger:** "Did you?"
- **Why it works:** Emotional/Cliffhanger beat (8.05/10): identity/lineage stakes land fast; intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 28.4 | 65.0 | Master in–out (cut this whole promo) |
| 2 | hook | 28.4 | 41.2 | Hook (opening lines) · scene_2 |
| 3 | rise | 41.2 | 53.0 | Escalation · scene_2 |
| 4 | cliffhanger | 53.0 | 65.0 | Cliffhanger (exit line) · scene_2 |

### Episode 45

*Logline:* Alexander frees Juliana from her chains and proclaims her the Duchess of Ashburton before the stunned congregation, only for an ecclesiastical authority to burst in and declare their marriage legally invalid.

**Cut:** `01:26.500` → `02:01.750` (35.2s) | **In campaign pack:** no | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger', 'romantic']

- **Hook:** "No one will bow yet!"
- **Cliffhanger:** "You are not Alexander Ashburton's lawful wife."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): intimacy and danger collide; physical peril raises binge urgency.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 86.5 | 121.75 | Master in–out (cut this whole promo) |
| 2 | hook | 86.5 | 86.5 | Hook · scene_2 |
| 3 | cliffhanger | 86.5 | 121.75 | Cliffhanger · scene_3 |

### Episode 46

*Logline:* The High Priest places the sanctuary under Crown seizure and invalidates Alexander and Juliana's wedding for lack of royal license, prompting Alexander to demand a ten-day ecclesiastical trial while Catherine schemes to destroy them.

**Cut:** `00:34.300` → `01:11.000` (36.7s) | **In campaign pack:** no | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger', 'romantic']

- **Hook:** "She married the man... not the title."
- **Cliffhanger:** "Love doesn't make a Duchess, girl. Paper does."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast; intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 34.3 | 71.0 | Master in–out (cut this whole promo) |
| 2 | hook | 34.3 | 47.0 | Hook (opening lines) · scene_1 |
| 3 | rise | 47.0 | 58.0 | Escalation · scene_1 |
| 4 | cliffhanger | 58.0 | 71.0 | Cliffhanger (exit line) · scene_1 |

### Episode 47

*Logline:* While Alexander reassures Juliana of their unbreakable bond amid the council's opposition, a destitute Catherine begs for sanctuary at Ashbourne—only for Juliana to offer her survival under the strict humiliation of a scullery maid.

**Cut:** `00:21.500` → `00:54.800` (33.3s) | **In campaign pack:** no | **ep_score:** 7.86/10 | **types:** ['emotional', 'cliffhanger', 'romantic']

- **Hook:** "What if Father Thomas sways the High Council?"
- **Cliffhanger:** "You were my wife before that priest ever opened his mouth. And we will stand before the King and God again within ten days. Nothing breaks that."
- **Why it works:** Emotional/Cliffhanger beat (7.86/10): identity/lineage stakes land fast; open question pulls the next click.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 21.5 | 54.8 | Master in–out (cut this whole promo) |
| 2 | hook | 21.5 | 21.5 | Hook · scene_1 |
| 3 | cliffhanger | 21.5 | 54.8 | Cliffhanger · scene_2 |

### Episode 48

*Logline:* While feigning submission after her public humiliation, Catherine schemes in secret, plotting to use the council's ten-day reprieve to strike back at Alexander and Juliana with the aid of Father Thomas.

**Cut:** `00:26.700` → `00:43.000` (16.3s) | **In campaign pack:** no | **ep_score:** 6.79/10 | **types:** ['conflict']

- **Hook:** "You sent for me, my lady?"
- **Cliffhanger:** "Grief makes people careless, and carelessness is exactly what I need from that household right now."
- **Why it works:** Conflict beat (6.79/10): open question pulls the next click.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 26.7 | 43.0 | Master in–out (cut this whole promo) |
| 2 | hook | 26.7 | 26.7 | Hook · scene_1 |
| 3 | cliffhanger | 26.7 | 43.0 | Cliffhanger · scene_2 |

### Episode 49

*Logline:* Meeting Father Thomas in an abandoned wing of the manor before dawn, Catherine orchestrates a calculated conspiracy to stall the council hearing and extract inside intelligence, sealing their treasonous alliance with intimate assurance.

**Cut:** `01:02.800` → `01:52.800` (50.0s) | **In campaign pack:** no | **ep_score:** 6.56/10 | **types:** ['conflict']

- **Hook:** "And you always did have a taste for using me. It's why we suit each other."
- **Cliffhanger:** "If I keep the hearing open, if I feed you every word spoken behind those doors, what happens to me when the Duke finds out a crowned priest conspired agains...
- **Why it works:** Conflict beat (6.56/10): identity/lineage stakes land fast; intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 62.8 | 112.8 | Master in–out (cut this whole promo) |
| 2 | hook | 62.8 | 77.0 | Hook (opening lines) · scene_1 |
| 3 | rise | 77.0 | 94.0 | Escalation · scene_1 |
| 4 | cliffhanger | 94.0 | 112.8 | Cliffhanger (exit line) · scene_1 |

### Episode 50

*Logline:* Following their illicit passion in the abandoned manor wing, Catherine negotiates Father Thomas's corrupt silence with territorial control—unaware that Agnes has walked in and witnessed their scandalous intimacy.

**Cut:** `00:31.000` → `01:10.500` (39.5s) | **In campaign pack:** no | **ep_score:** 6.56/10 | **types:** ['romantic']

- **Hook:** "Absolution is free. Discretion has a price."
- **Cliffhanger:** "Or perhaps discretion isn't the only thing you've developed a taste for."
- **Why it works:** Romantic beat (6.56/10): identity/lineage stakes land fast; intimacy and danger collide.

| Seg | Role | Start (s) | End (s) | Label |
|----:|------|----------:|--------:|-------|
| 1 | full_window | 31.0 | 70.5 | Master in–out (cut this whole promo) |
| 2 | hook | 31.0 | 70.5 | Hook · scene_1 |
| 3 | cliffhanger | 70.5 | 70.5 | Cliffhanger · scene_2 |

---

## C. Editor summary

Lead the campaign with:

1. **Ep 3** — acquisition — global 8.68 — I didn't steal what was never truly yours.
2. **Ep 32** — climax — global 8.616 — "And a woman who never embarrasses the people standing behind her."
3. **Ep 35** — climax — global 8.401 — "I survived because the men who came looking for me believed I was alr
4. **Ep 44** — payoff — global 8.485 — "Do you know what this did to me?"
5. **Ep 11** — bonding — global 8.465 — "Your husband stole my gold pocket watch!"
6. **Ep 35** — climax — global 8.531 — "Then how did you survive?"
7. **Ep 2** — acquisition — global 8.383 — "Surely you will not let him humiliate me like this?"
8. **Ep 9** — bonding — global 8.149 — "Then we will face it together."

Ranking uses **Series Continuity Map** + intrinsic quality + standalone clarity. **Promo classification labels never enter the score** — they stay on cards so marketers can A/B every kind. Pack size is user `--top-n` or auto 20–30 from score floor + elbow.
