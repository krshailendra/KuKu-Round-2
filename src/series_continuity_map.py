"""Series Continuity Map — whole-show context derived from all episode inputs.

Not a "bible": a living map of spine, characters, arc phases, and recurring
themes built only from processed episode data + series_context loglines.
Used to:
  - ground global promo scoring in series meaning
  - tag promos with theme affinity (for reporting / diversity)
  - NEVER as a hard filter that kills promo-type variety for marketers
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple


# Display / product name (avoid "bible")
CONTINUITY_MAP_NAME = "Series Continuity Map"
CONTINUITY_MAP_SLUG = "series_continuity_map"


# Seed spine themes for this romantic-drama show; refined by corpus counts.
THEME_DEFS: Dict[str, Dict[str, Any]] = {
    "wedding_betrayal": {
        "label": "Wedding / betrayal",
        "weight": 1.0,
        "keywords": [
            "bridal", "wedding", "cathedral", "betray", "groom", "altar",
            "gown", "fiancé", "fiance", "marry", "marriage", "vows",
        ],
    },
    "identity_lineage": {
        "label": "Identity / lineage",
        "weight": 0.95,
        "keywords": [
            "father", "mother", "daughter", "duke", "ducal", "heir", "blood",
            "legacy", "name", "title", "bastard", "true daughter",
        ],
    },
    "central_bond": {
        "label": "Central bond (Juliana ↔ Alexander)",
        "weight": 0.9,
        "keywords": [
            "alexander", "juliana", "embrace", "kiss", "love", "protect",
            "hearth", "hold me", "stay with", "i love",
        ],
    },
    "violence_peril": {
        "label": "Violence / peril",
        "weight": 0.85,
        "keywords": [
            "wound", "blood", "attack", "assault", "kill", "sword", "injured",
            "dying", "poison", "bleed", "stab", "shot",
        ],
    },
    "power_disownment": {
        "label": "Power / disownment",
        "weight": 0.9,
        "keywords": [
            "disown", "inheritance", "cast out", "never", "get out", "estate",
            "claim", "seat", "worthless", "nothing to offer",
        ],
    },
    "secret_truth": {
        "label": "Secret / truth reveal",
        "weight": 0.8,
        "keywords": [
            "truth", "secret", "lied", "reveal", "confession", "promise",
            "never tell", "hid", "knew",
        ],
    },
    "home_garden": {
        "label": "Home / garden refuge",
        "weight": 0.55,
        "keywords": ["garden", "cottage", "home", "hearth", "flowers"],
    },
    "rival_court": {
        "label": "Rival / court society",
        "weight": 0.7,
        "keywords": [
            "clarissa", "gerald", "matriarch", "noble", "ball", "county",
            "society", "gossip", "humiliat",
        ],
    },
}


def _load_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _ep_path(ep: int, processed_dir: str) -> str:
    p = os.path.join(processed_dir, f"ep_{ep:03d}.json")
    if os.path.exists(p):
        return p
    return os.path.join(processed_dir, f"ep_{ep}.json")


def _theme_hits(text: str) -> Dict[str, int]:
    t = (text or "").lower()
    hits = {}
    for tid, meta in THEME_DEFS.items():
        c = sum(1 for k in meta["keywords"] if k in t)
        if c:
            hits[tid] = c
    return hits


def _arc_phase(ep: int, total: int) -> str:
    if total <= 1:
        return "opening"
    p = (ep - 1) / (total - 1)
    if p <= 0.12:
        return "opening"
    if p <= 0.30:
        return "binding"
    if p <= 0.55:
        return "rising"
    if p <= 0.78:
        return "peak"
    return "resolution"


def build_continuity_map(
    processed_dir: str = "data/processed",
    series_context_path: str = "data/processed/series_context.json",
    max_episodes: int = 50,
) -> Dict[str, Any]:
    """Build Series Continuity Map from all episode inputs."""
    ctx = _load_json(series_context_path) or {}
    loglines_raw = ctx.get("loglines") or []
    ll_map: Dict[int, str] = {}
    for row in loglines_raw:
        try:
            ll_map[int(row["ep"])] = row.get("logline") or ""
        except (KeyError, TypeError, ValueError):
            continue

    # Discover episode files
    eps_found = []
    for n in range(1, max_episodes + 1):
        if os.path.exists(_ep_path(n, processed_dir)):
            eps_found.append(n)
    if not eps_found and ll_map:
        eps_found = sorted(ll_map.keys())

    total = max(eps_found) if eps_found else int(ctx.get("total_episodes") or 50)

    theme_corpus = Counter()
    name_mentions = Counter()
    episode_rows: List[Dict[str, Any]] = []
    all_logline_text = []

    # Light name harvest from dialogue-ish words
    name_re = re.compile(
        r"\b(Juliana|Alexander|Gerald|Clarissa|Agnes|Catherine|Matriarch)\b",
        re.I,
    )

    for ep in eps_found:
        data = _load_json(_ep_path(ep, processed_dir)) or {}
        logline = data.get("logline") or ll_map.get(ep, "")
        ll_map.setdefault(ep, logline)
        all_logline_text.append(logline)

        # Sample beat text (cap for speed)
        beat_bits = []
        for sc in (data.get("scenes") or [])[:12]:
            for b in (sc.get("beats") or [])[:40]:
                tx = (b.get("text") or "").strip()
                if tx:
                    beat_bits.append(tx[:200])
                    for m in name_re.findall(tx):
                        name_mentions[m.title()] += 1
        sample = " ".join(beat_bits[:80])
        blob = f"{logline} {sample}"
        hits = _theme_hits(blob)
        for tid, c in hits.items():
            theme_corpus[tid] += c

        episode_rows.append(
            {
                "episode": ep,
                "logline": logline,
                "arc_phase": _arc_phase(ep, total),
                "theme_hits": hits,
                "primary_themes": sorted(hits.keys(), key=lambda k: -hits[k])[:3],
            }
        )

    # Theme ranking from corpus
    themes_ranked = []
    for tid, meta in THEME_DEFS.items():
        count = int(theme_corpus.get(tid, 0))
        themes_ranked.append(
            {
                "id": tid,
                "label": meta["label"],
                "spine_weight": meta["weight"],
                "corpus_hits": count,
                "keywords": meta["keywords"][:8],
            }
        )
    themes_ranked.sort(key=lambda x: (-x["spine_weight"] * (1 + x["corpus_hits"] ** 0.5), -x["corpus_hits"]))

    # Arc phases summary
    phases = defaultdict(list)
    for row in episode_rows:
        phases[row["arc_phase"]].append(row["episode"])

    # One-line series logline from ep1 + dominant themes
    top_theme_labels = [t["label"] for t in themes_ranked[:4]]
    series_one_liner = (
        (ll_map.get(1) or "A high-stakes romantic drama.")[:180]
        + f" Dominant threads: {', '.join(top_theme_labels)}."
    )

    principals = [
        {"name": n, "mentions": c}
        for n, c in name_mentions.most_common(12)
    ]

    # Spoiler sensitivity: late resolution eps more spoilery for cold posts
    spoiler_guidance = {
        "cold_safe_phases": ["opening", "binding"],
        "use_sparingly_for_acquisition": ["peak", "resolution"],
        "note": (
            "Late-arc reveals (identity payoffs, final confrontations) score well "
            "for quality but carry spoiler risk for cold traffic — global ranker "
            "applies a soft penalty when campaign_role is acquisition-facing."
        ),
    }

    doc = {
        "name": CONTINUITY_MAP_NAME,
        "slug": CONTINUITY_MAP_SLUG,
        "version": 1,
        "total_episodes": total,
        "episodes_indexed": len(episode_rows),
        "series_one_liner": series_one_liner,
        "principals": principals,
        "spine_themes": themes_ranked,
        "arc_phases": {k: sorted(v) for k, v in phases.items()},
        "episodes": episode_rows,
        "loglines": [{"ep": e, "logline": ll_map.get(e, "")} for e in sorted(ll_map.keys())],
        "spoiler_guidance": spoiler_guidance,
        "promo_theme_taxonomy_note": (
            "Promo classification labels (emotional, cliffhanger, …) are editorial "
            "tags for marketers to experiment with mix — they must not drive rank. "
            "Continuity themes below are story-spine signals for fit/clarity only."
        ),
        "how_to_use": {
            "global_scoring": "Fit promo text + ep logline against spine_themes + arc_phase",
            "campaign_pack": "Rank all candidates globally; diversify types AFTER score",
            "per_episode_catalogue": "Still pick best-in-ep for episode pages",
        },
    }
    return doc


def save_continuity_map(
    out_path: str = "data/processed/series_continuity_map.json",
    **kwargs: Any,
) -> Dict[str, Any]:
    doc = build_continuity_map(**kwargs)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    return doc


def load_continuity_map(
    path: str = "data/processed/series_continuity_map.json",
    rebuild_if_missing: bool = True,
) -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    if rebuild_if_missing:
        return save_continuity_map(out_path=path)
    return build_continuity_map()


def theme_affinity(text: str, continuity: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """0–1 affinity per spine theme (not promo_types)."""
    hits = _theme_hits(text)
    if not hits:
        return {}
    mx = max(hits.values()) or 1
    return {k: round(v / mx, 3) for k, v in hits.items()}


def primary_continuity_themes(text: str, top_n: int = 3) -> List[str]:
    hits = _theme_hits(text)
    return [k for k, _ in sorted(hits.items(), key=lambda kv: -kv[1])[:top_n]]


def arc_phase_for_episode(ep: int, continuity: Optional[Dict[str, Any]] = None) -> str:
    total = 50
    if continuity:
        total = int(continuity.get("total_episodes") or 50)
    return _arc_phase(int(ep), total)
