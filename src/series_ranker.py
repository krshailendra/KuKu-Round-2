"""Global series-level ranking for storytelling promos.

Two jobs:
  1) Score ANY promo (not only per-ep champions) with a global series score
     grounded in the Series Continuity Map.
  2) Build a campaign pack (top N) with diversity — WITHOUT ranking by
     promo classification labels (marketers need to experiment with all kinds).

Per-episode overall_score stays local. series_global_score is cross-episode.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from src.series_continuity_map import (
    CONTINUITY_MAP_NAME,
    arc_phase_for_episode,
    load_continuity_map,
    primary_continuity_themes,
    theme_affinity,
)


def load_series_context(path: str = "data/processed/series_context.json") -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"total_episodes": 50, "loglines": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def logline_map(ctx: Dict[str, Any]) -> Dict[int, str]:
    out = {}
    for row in ctx.get("loglines") or []:
        try:
            out[int(row["ep"])] = row.get("logline") or ""
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _f(x, default=0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def _norm_score(x: float) -> float:
    """Normalize possible 0–1 LLM scores to 0–10."""
    v = _f(x, 0.0)
    if 0 < v <= 1.5:
        v *= 10.0
    return max(0.0, min(10.0, v))


def _text_blob(promo: Dict[str, Any], logline: str = "") -> str:
    parts = [
        promo.get("trigger_text") or "",
        promo.get("window_text") or "",
        promo.get("hook") or "",
        promo.get("cliffhanger") or "",
        promo.get("llm_rationale") or "",
        logline or "",
    ]
    return " ".join(parts).lower()


def continuity_fit(text: str, continuity: Dict[str, Any]) -> float:
    """0–10: how strongly the clip touches Series Continuity Map spine themes.

    Uses story themes from the map — NOT promo_types labels.
    """
    aff = theme_affinity(text)
    if not aff:
        return 3.5
    spine = continuity.get("spine_themes") or []
    weight_by_id = {t["id"]: float(t.get("spine_weight") or 0.5) for t in spine}
    # default weights if map empty
    if not weight_by_id:
        from src.series_continuity_map import THEME_DEFS

        weight_by_id = {k: float(v["weight"]) for k, v in THEME_DEFS.items()}

    score = 0.0
    for tid, a in aff.items():
        score += a * weight_by_id.get(tid, 0.5)
    # normalize roughly
    max_possible = sum(sorted(weight_by_id.values(), reverse=True)[:3]) or 1.0
    return round(min(10.0, 3.0 + (score / max_possible) * 7.0), 2)


def standalone_clarity(promo: Dict[str, Any], logline: str = "") -> float:
    """0–10: cold viewer understands stakes without binge homework."""
    text = (promo.get("trigger_text") or "") + " " + (promo.get("window_text") or "")
    t = text.lower()
    score = 5.0
    clear = [
        "betray", "wedding", "father", "mother", "disown", "marry", "kill",
        "love you", "don't die", "get out", "never", "truth", "duke", "blood",
        "how dare", "i swear", "protect", "accept my hand", "poison",
    ]
    score += min(3.0, 0.7 * sum(1 for c in clear if c in t))
    if any(n in t for n in ("juliana", "alexander", "gerald", "clarissa", "agnes")):
        score += 0.8
    if "?" in text:
        score += 0.6
    words = text.split()
    if len(words) < 8 and not any(c in t for c in clear):
        score -= 1.5
    if logline and any(k in t for k in ("betray", "wedding", "wound", "father", "duke")):
        score += 0.4
    return round(max(0.0, min(10.0, score)), 2)


def campaign_role(episode: int, total_eps: int = 50) -> Tuple[str, float]:
    """Arc position → campaign role + soft bonus (not a hard gate)."""
    if total_eps <= 1:
        return "acquisition", 8.0
    p = (episode - 1) / (total_eps - 1)
    if p <= 0.12:
        return "acquisition", 9.0
    if p <= 0.30:
        return "bonding", 8.3
    if p <= 0.55:
        return "escalation", 8.0
    if p <= 0.78:
        return "climax", 8.4
    return "payoff", 6.8


def duration_fit(duration: float) -> float:
    d = float(duration or 0)
    if 20 <= d <= 45:
        return 9.5
    if 15 <= d < 20 or 45 < d <= 55:
        return 8.0
    if 12 <= d < 15 or 55 < d <= 65:
        return 6.5
    return 5.0


def spoiler_risk(episode: int, total_eps: int, clarity: float, fit: float) -> float:
    """0–10 penalty-ish helper: higher = more spoiler-heavy for cold open.

    Returned as a soft subtractor scale later — late + high fit + low clarity
    is riskiest to lead with.
    """
    p = 0.0 if total_eps <= 1 else (episode - 1) / (total_eps - 1)
    risk = 0.0
    if p > 0.75:
        risk += 2.5
    elif p > 0.55:
        risk += 1.2
    if clarity < 6.0:
        risk += 1.0
    if fit >= 8.0 and p > 0.7:
        risk += 0.8  # big spine payoffs late
    return min(5.0, risk)


def compute_global_score(
    promo: Dict[str, Any],
    logline: str = "",
    continuity: Optional[Dict[str, Any]] = None,
    total_eps: int = 50,
) -> Dict[str, Any]:
    """Global series score for one promo. Does NOT use promo_types in the formula.

    Marketers experiment with all classification labels; labels are tags only.
    """
    continuity = continuity or load_continuity_map()
    overall = _norm_score(_f(promo.get("overall_score"), 5.0))
    hook = _norm_score(_f(promo.get("hook_strength"), overall))
    cliff = _norm_score(_f(promo.get("cliffhanger_strength"), overall))
    # optional other dims if present
    emotional = _norm_score(_f(promo.get("emotional_impact"), overall * 0.9))
    narrative = _norm_score(_f(promo.get("narrative_completeness"), overall * 0.9))

    text = _text_blob(promo, logline)
    fit = continuity_fit(text, continuity)
    clarity = standalone_clarity(promo, logline)
    ep = int(promo.get("episode") or 1)
    role_name, role_bonus = campaign_role(ep, total_eps)
    dur = duration_fit(_f(promo.get("duration_sec"), 30))
    risk = spoiler_risk(ep, total_eps, clarity, fit)

    # Intrinsic quality dominates; continuity fit & clarity are series-aware.
    # Explicitly excluded: promo_types / classification labels.
    raw = (
        0.26 * overall
        + 0.16 * hook
        + 0.16 * cliff
        + 0.08 * emotional
        + 0.06 * narrative
        + 0.14 * fit
        + 0.10 * clarity
        + 0.04 * role_bonus
        + 0.04 * dur
        - 0.06 * risk  # soft spoiler dampener
    )

    # Small boosts that are still type-agnostic
    if role_name == "acquisition" and clarity >= 7.0:
        raw += 0.2
    if fit >= 8.0 and hook >= 7.0:
        raw += 0.12

    series_global_score = round(min(10.0, max(0.0, raw)), 3)
    themes = primary_continuity_themes(text, top_n=3)

    return {
        "series_global_score": series_global_score,
        # alias used by older deliverable paths
        "series_score": series_global_score,
        "breakdown": {
            "overall": round(overall, 2),
            "hook": round(hook, 2),
            "cliff": round(cliff, 2),
            "emotional": round(emotional, 2),
            "narrative": round(narrative, 2),
            "continuity_fit": fit,
            "standalone_clarity": clarity,
            "campaign_role": role_name,
            "campaign_role_bonus": role_bonus,
            "duration_fit": dur,
            "spoiler_risk": risk,
            "continuity_themes": themes,
            "arc_phase": arc_phase_for_episode(ep, continuity),
            # stored for reporting only — NOT used in score
            "promo_types_tag": list(promo.get("promo_types") or []),
        },
    }


# Back-compat name
def compute_series_score(
    promo: Dict[str, Any],
    logline: str = "",
    total_eps: int = 50,
    continuity: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    meta = compute_global_score(promo, logline=logline, continuity=continuity, total_eps=total_eps)
    return {
        "series_score": meta["series_global_score"],
        "breakdown": meta["breakdown"],
    }


def score_all_promos(
    promos: List[Dict[str, Any]],
    continuity: Optional[Dict[str, Any]] = None,
    series_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Attach series_global_score to every promo in the pool."""
    continuity = continuity or load_continuity_map()
    ctx = series_context or load_series_context()
    ll_map = logline_map(ctx)
    # prefer continuity loglines if richer
    for row in continuity.get("loglines") or []:
        try:
            ll_map[int(row["ep"])] = row.get("logline") or ll_map.get(int(row["ep"]), "")
        except (KeyError, TypeError, ValueError):
            continue
    total = int(continuity.get("total_episodes") or ctx.get("total_episodes") or 50)

    scored = []
    for p in promos:
        ep = int(p.get("episode") or 0)
        ll = ll_map.get(ep, "")
        meta = compute_global_score(p, logline=ll, continuity=continuity, total_eps=total)
        row = dict(p)
        row["episode_logline"] = ll
        row["series_global_score"] = meta["series_global_score"]
        row["series_score"] = meta["series_global_score"]
        row["series_breakdown"] = meta["breakdown"]
        row["continuity_themes"] = meta["breakdown"].get("continuity_themes") or []
        scored.append(row)

    scored.sort(
        key=lambda r: (
            r["series_global_score"],
            _f(r.get("overall_score")),
            _f(r.get("hook_strength")),
            -int(r.get("episode") or 0),
        ),
        reverse=True,
    )
    return scored


def auto_top_n(
    scored: List[Dict[str, Any]],
    min_n: int = 20,
    max_n: int = 30,
    floor: float = 6.4,
) -> int:
    """Decide campaign pack size when user does not pass --top-n.

    Criteria (in order):
      1. Keep scores above a soft floor
      2. Prefer elbow where score drop between consecutive items spikes
      3. Clamp to [min_n, max_n]
      4. Prefer more items if many near-tied high scores (rich pool)
    """
    if not scored:
        return 0
    n_pool = len(scored)
    if n_pool <= min_n:
        return n_pool

    # candidates above floor
    above = [p for p in scored if _f(p.get("series_global_score")) >= floor]
    if len(above) < min_n:
        # lower floor slightly
        above = scored[: max(min_n, min(max_n, n_pool))]
    # elbow on top max_n+5 window
    window = scored[: min(n_pool, max_n + 8)]
    best_n = min_n
    best_drop = -1.0
    for i in range(min_n, min(len(window), max_n + 1)):
        if i >= len(window):
            break
        prev = _f(window[i - 1].get("series_global_score"))
        cur = _f(window[i].get("series_global_score"))
        drop = prev - cur
        # also reward staying above floor
        if cur < floor - 0.35:
            drop += 0.15  # encourage cutting here
        if drop > best_drop:
            best_drop = drop
            best_n = i

    # rich high-score pool → push toward max_n
    high = sum(1 for p in scored if _f(p.get("series_global_score")) >= 7.5)
    if high >= 28:
        best_n = max(best_n, min(max_n, 28))
    elif high >= 22:
        best_n = max(best_n, min(max_n, 24))

    # if many above floor, don't cut too aggressively
    n_above = len([p for p in scored if _f(p.get("series_global_score")) >= floor])
    if n_above >= max_n:
        best_n = max(best_n, max_n)
    else:
        best_n = max(min_n, min(best_n, max(n_above, min_n)))

    return int(max(min_n, min(max_n, best_n, n_pool)))


def diversity_pack(
    scored: List[Dict[str, Any]],
    top_n: int,
    max_per_episode: int = 2,
    type_repeat_soft: float = 0.10,
    theme_repeat_soft: float = 0.08,
    ep_neighbor_soft: float = 0.06,
) -> List[Dict[str, Any]]:
    """Greedy pack: order by global score, soft-penalize repeats.

    IMPORTANT:
      - promo_types never enter the *score*
      - type_repeat_soft only affects *ordering within the pack* so marketers
        still get a mix to experiment with — not a type leaderboard
      - max_per_episode stops one ep from owning the feed
    """
    if top_n <= 0 or not scored:
        return []

    remaining = list(scored)
    out: List[Dict[str, Any]] = []
    ep_counts: Dict[int, int] = {}
    type_counts: Dict[str, int] = {}
    theme_counts: Dict[str, int] = {}
    recent_eps: List[int] = []

    while remaining and len(out) < top_n:
        best_i = 0
        best_adj = -1e9
        for i, item in enumerate(remaining):
            base = _f(item.get("series_global_score"))
            ep = int(item.get("episode") or 0)
            if ep_counts.get(ep, 0) >= max_per_episode:
                continue  # hard cap per ep

            adj = base
            # soft type mix (tag only)
            types = item.get("promo_types") or ["untagged"]
            primary = types[0] if types else "untagged"
            adj -= type_repeat_soft * type_counts.get(primary, 0)

            # soft continuity-theme mix
            themes = item.get("continuity_themes") or (item.get("series_breakdown") or {}).get(
                "continuity_themes"
            ) or []
            for th in themes[:2]:
                adj -= theme_repeat_soft * theme_counts.get(th, 0)

            # avoid adjacent-ep clustering in top of pack
            for prev in recent_eps[-3:]:
                if abs(prev - ep) <= 2:
                    adj -= ep_neighbor_soft

            # early pack: lightly prefer higher clarity (still type-agnostic)
            if len(out) < 5:
                clarity = _f((item.get("series_breakdown") or {}).get("standalone_clarity"), 5)
                if clarity >= 7.5:
                    adj += 0.08
                role = (item.get("series_breakdown") or {}).get("campaign_role")
                if role == "payoff" and clarity < 7.0:
                    adj -= 0.15

            if adj > best_adj:
                best_adj = adj
                best_i = i

        # if all remaining blocked by max_per_episode, relax once
        if best_adj < -1e8:
            # pick best remaining by raw score ignoring ep cap
            best_i = 0
            best_adj = _f(remaining[0].get("series_global_score"))
            for i, item in enumerate(remaining):
                s = _f(item.get("series_global_score"))
                if s > best_adj:
                    best_adj = s
                    best_i = i

        chosen = dict(remaining.pop(best_i))
        chosen["campaign_rank"] = len(out) + 1
        chosen["post_rank"] = chosen["campaign_rank"]
        chosen["adjusted_series_score"] = round(best_adj, 3)
        out.append(chosen)

        ep = int(chosen.get("episode") or 0)
        ep_counts[ep] = ep_counts.get(ep, 0) + 1
        types = chosen.get("promo_types") or ["untagged"]
        primary = types[0] if types else "untagged"
        type_counts[primary] = type_counts.get(primary, 0) + 1
        themes = chosen.get("continuity_themes") or []
        for th in themes[:2]:
            theme_counts[th] = theme_counts.get(th, 0) + 1
        recent_eps.append(ep)

    return out


def build_campaign_pack(
    promos: List[Dict[str, Any]],
    top_n: Optional[int] = None,
    min_n: int = 20,
    max_n: int = 30,
    max_per_episode: int = 2,
    continuity: Optional[Dict[str, Any]] = None,
    series_context: Optional[Dict[str, Any]] = None,
    marketer_trim: bool = True,
    marketer_min_keep: int = 12,
    marketer_max_keep: int = 24,
    marketer_use_llm: bool = False,
) -> Dict[str, Any]:
    """Score full pool → choose N → diversity pack → Marketer Agent trim.

    Marketer removes weak tail (thin hooks, bad segments, low clarity) but
    never cuts protected strong promos.
    """
    from src.marketer_agent import run_marketer_agent

    continuity = continuity or load_continuity_map()
    scored = score_all_promos(promos, continuity=continuity, series_context=series_context)

    auto = False
    if top_n is None or int(top_n) <= 0:
        top_n = auto_top_n(scored, min_n=min_n, max_n=max_n)
        auto = True
    else:
        top_n = int(top_n)
        top_n = max(1, min(top_n, len(scored)))

    pack = diversity_pack(scored, top_n=top_n, max_per_episode=max_per_episode)
    pre_marketer_n = len(pack)

    marketer_meta: Dict[str, Any] = {
        "enabled": marketer_trim,
        "cut_count": 0,
        "kept": pre_marketer_n,
        "cut_list": [],
    }
    if marketer_trim and pack:
        m = run_marketer_agent(
            pack,
            min_keep=marketer_min_keep,
            max_keep=min(marketer_max_keep, max(marketer_min_keep, top_n)),
            target_keep=None,
            use_llm=marketer_use_llm,
            continuity_one_liner=str(continuity.get("series_one_liner") or ""),
        )
        pack = m.get("campaign_pack") or pack
        marketer_meta = {
            "enabled": True,
            "kept": m.get("kept"),
            "cut_count": m.get("cut_count"),
            "protected_count": m.get("protected_count"),
            "min_keep": m.get("min_keep"),
            "max_keep": m.get("max_keep"),
            "cut_list": m.get("cut_list") or [],
            "marketer_note": m.get("marketer_note"),
            "pre_marketer_n": pre_marketer_n,
            "llm_votes": m.get("llm_votes"),
        }

    # type mix stats for marketers (reporting only)
    type_mix: Dict[str, int] = {}
    theme_mix: Dict[str, int] = {}
    ep_set = set()
    for p in pack:
        for t in p.get("promo_types") or ["untagged"]:
            type_mix[t] = type_mix.get(t, 0) + 1
        for th in p.get("continuity_themes") or []:
            theme_mix[th] = theme_mix.get(th, 0) + 1
        ep_set.add(int(p.get("episode") or 0))

    return {
        "continuity_map_name": CONTINUITY_MAP_NAME,
        "pool_size": len(scored),
        "top_n": top_n,
        "top_n_after_marketer": len(pack),
        "top_n_auto": auto,
        "top_n_rule": (
            f"auto elbow+floor in [{min_n},{max_n}] then marketer trim"
            if auto
            else f"user-requested N={top_n} then marketer trim"
        ),
        "max_per_episode": max_per_episode,
        "ranking_excludes_promo_types": True,
        "ranking_note": (
            "series_global_score ignores classification labels (emotional/cliffhanger/…). "
            "Types are tags for experiment mix; soft diversity only after scoring. "
            "Marketer agent trims weak hooks without removing protected strong promos."
        ),
        "type_mix": type_mix,
        "continuity_theme_mix": theme_mix,
        "episodes_represented": sorted(ep_set),
        "marketer": marketer_meta,
        "scored_pool_head": [
            {
                "episode": p.get("episode"),
                "series_global_score": p.get("series_global_score"),
                "overall_score": p.get("overall_score"),
                "promo_types": p.get("promo_types"),
                "continuity_themes": p.get("continuity_themes"),
                "start_sec": p.get("start_sec"),
                "end_sec": p.get("end_sec"),
            }
            for p in scored[:50]
        ],
        "campaign_pack": pack,
        "all_scored": scored,
    }


def rank_series_champions(
    champions: List[Dict[str, Any]],
    series_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Back-compat: rank one-per-episode champions for catalogue post-order."""
    pack = build_campaign_pack(
        champions,
        top_n=len(champions) if champions else 0,
        min_n=1,
        max_n=max(len(champions), 1),
        max_per_episode=1,
        series_context=series_context,
    )
    return pack["campaign_pack"]


def posting_why(item: Dict[str, Any]) -> str:
    bd = item.get("series_breakdown") or {}
    role = bd.get("campaign_role", "escalation")
    ep = item.get("episode")
    types = ", ".join(item.get("promo_types") or []) or "untagged"
    clarity = bd.get("standalone_clarity", 0)
    fit = bd.get("continuity_fit", bd.get("arc_centrality", 0))
    themes = ", ".join(item.get("continuity_themes") or bd.get("continuity_themes") or [])
    role_line = {
        "acquisition": "cold-open fuel — works without binge homework",
        "bonding": "locks the central relationship so new viewers care",
        "escalation": "raises stakes mid-arc; binge bait after the open pack",
        "climax": "peak tension for invested viewers",
        "payoff": "late-arc resonance — better after acquisition/bonding pack",
    }.get(role, "solid series beat")
    return (
        f"Ep {ep} · {role}: {role_line}. "
        f"Continuity fit {fit}/10, clarity {clarity}/10, "
        f"spine=[{themes}], tags=[{types}] (tags not scored), "
        f"global={item.get('series_global_score', item.get('series_score'))}."
    )
