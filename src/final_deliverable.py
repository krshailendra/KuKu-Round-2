"""Build the assignment-facing final deliverable from hybrid (or any) mode output.

For each episode:
  - best promo
  - ordered segments with start/end timestamps
  - hook
  - cliffhanger
  - one-line why it works

Then series-rank all 50 champions for "post first" order.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from src.series_continuity_map import (
    CONTINUITY_MAP_NAME,
    load_continuity_map,
    save_continuity_map,
)
from src.series_ranker import (
    build_campaign_pack,
    load_series_context,
    posting_why,
    rank_series_champions,
)


_EP_CACHE: Dict[int, Optional[Dict[str, Any]]] = {}


def _load_episode(ep: int, processed_dir: str = "data/processed") -> Optional[Dict[str, Any]]:
    if ep in _EP_CACHE:
        return _EP_CACHE[ep]
    path = os.path.join(processed_dir, f"ep_{ep:03d}.json")
    if not os.path.exists(path):
        path = os.path.join(processed_dir, f"ep_{ep}.json")
    if not os.path.exists(path):
        _EP_CACHE[ep] = None
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _EP_CACHE[ep] = data
    return data


def _beats_in_window(ep_data: Dict[str, Any], start: float, end: float) -> List[Dict[str, Any]]:
    beats = []
    for sc in ep_data.get("scenes") or []:
        sid = sc.get("id") or sc.get("scene_id") or ""
        for b in sc.get("beats") or []:
            bs = float(b.get("start_sec") or 0)
            be = float(b.get("end_sec") or bs)
            # overlap with window
            if be < start or bs > end:
                continue
            row = dict(b)
            row["_scene_id"] = sid
            beats.append(row)
    beats.sort(key=lambda x: float(x.get("start_sec") or 0))
    return beats


def _is_dialoguey(text: str, btype: str = "") -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if (btype or "").upper() == "DIALOGUE":
        return True
    if any(q in t for q in ('"', "“", "«")):
        return True
    # first-person / second-person short lines
    low = t.lower()
    if any(low.startswith(p) for p in ("i ", "you ", "we ", "don't", "do you", "how ", "why ")):
        return True
    return False


def extract_hook_and_cliff(
    promo: Dict[str, Any],
    ep_data: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """Pick a hook line (open) and cliffhanger line (close) from the window."""
    start = float(promo.get("start_sec") or 0)
    end = float(promo.get("end_sec") or start)
    window = (promo.get("window_text") or "").strip()
    trigger = (promo.get("trigger_text") or "").strip()

    dialogue_lines: List[Tuple[float, str]] = []
    if ep_data:
        for b in _beats_in_window(ep_data, start, end):
            text = (b.get("text") or "").strip()
            if not text:
                continue
            if _is_dialoguey(text, b.get("type") or ""):
                # strip stage directions lightly
                clean = text
                if len(clean) > 160:
                    clean = clean[:157] + "..."
                dialogue_lines.append((float(b.get("start_sec") or 0), clean))

    hook = ""
    cliff = ""
    if dialogue_lines:
        hook = dialogue_lines[0][1]
        cliff = dialogue_lines[-1][1]
        if len(dialogue_lines) >= 2:
            # First punchy line as hook
            for _, line in dialogue_lines:
                if "?" in line or "!" in line or _is_dialoguey(line, "DIALOGUE"):
                    hook = line
                    break
            # Last punchy line as cliff (prefer different from hook)
            for _, line in reversed(dialogue_lines):
                if line.strip() == hook.strip():
                    continue
                if any(x in line for x in ("?", "!", "…", "...")) or _is_dialoguey(line, "DIALOGUE"):
                    cliff = line
                    break
            if cliff.strip() == hook.strip():
                cliff = dialogue_lines[-1][1]

    if not hook:
        hook = trigger or (window[:140] if window else "")
    if not cliff:
        # last sentence of window
        parts = re.split(r"(?<=[.!?])\s+", window)
        cliff = (parts[-1] if parts else trigger) or hook
        if len(cliff) > 160:
            cliff = cliff[:157] + "..."

    # Avoid identical hook/cliff when possible
    if cliff.strip() == hook.strip() and window and len(window) > len(hook) + 20:
        parts = re.split(r"(?<=[.!?])\s+", window)
        if len(parts) >= 2:
            cliff = parts[-1][:160]

    hook_s, cliff_s = hook.strip(), cliff.strip()
    # Soft length caps for deliverable readability
    if len(hook_s) > 180:
        hook_s = hook_s[:177] + "..."
    if len(cliff_s) > 180:
        cliff_s = cliff_s[:177] + "..."
    return hook_s, cliff_s


def build_segments(
    promo: Dict[str, Any],
    ep_data: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Ordered cut segments for the promo (assignment: every segment start/end).

    Strategy:
      1. Continuous window is always segment 0 (master in/out).
      2. If multiple scenes overlap the window → one segment per scene run.
      3. Else split by dialogue beats into hook / rise / cliff using beat
         timestamps (not blind thirds) when we have ≥3 dialogue beats.
    """
    start = float(promo.get("start_sec") or 0)
    end = float(promo.get("end_sec") or start)
    master = {
        "index": 1,
        "role": "full_window",
        "scene_id": (promo.get("scene_ids") or ["unknown"])[0],
        "start_sec": round(start, 2),
        "end_sec": round(end, 2),
        "label": "Master in–out (cut this whole promo)",
    }

    if not ep_data:
        return [master]

    beats = _beats_in_window(ep_data, start, end)
    if not beats:
        return [master]

    # Scene runs
    groups: List[Dict[str, Any]] = []
    cur_scene = cur_start = cur_end = None
    for b in beats:
        sid = b.get("_scene_id") or "scene"
        bs = max(start, float(b.get("start_sec") or start))
        be = min(end, float(b.get("end_sec") or bs))
        if cur_scene is None:
            cur_scene, cur_start, cur_end = sid, bs, be
        elif sid == cur_scene and bs <= (cur_end or 0) + 1.5:
            cur_end = max(cur_end or bs, be)
        else:
            groups.append({"scene_id": cur_scene, "start_sec": cur_start, "end_sec": cur_end})
            cur_scene, cur_start, cur_end = sid, bs, be
    if cur_scene is not None:
        groups.append({"scene_id": cur_scene, "start_sec": cur_start, "end_sec": cur_end})

    segments: List[Dict[str, Any]] = [master]

    if len(groups) >= 2:
        for i, g in enumerate(groups):
            role = "hook" if i == 0 else ("cliffhanger" if i == len(groups) - 1 else "rise")
            segments.append(
                {
                    "index": len(segments) + 1,
                    "role": role,
                    "scene_id": g["scene_id"],
                    "start_sec": round(float(g["start_sec"]), 2),
                    "end_sec": round(float(g["end_sec"]), 2),
                    "label": f"{role.title()} · {g['scene_id']}",
                }
            )
        return segments

    # Single scene: dialogue-anchored hook / rise / cliff
    dlg = [
        b
        for b in beats
        if _is_dialoguey((b.get("text") or ""), b.get("type") or "")
        or (b.get("text") or "").strip()
    ]
    g = groups[0]
    s, e = float(g["start_sec"]), float(g["end_sec"])
    d = max(0.1, e - s)

    if len(dlg) >= 3 and d >= 15:
        # hook: first third of dialogue beats; cliff: last third
        n = len(dlg)
        i1 = max(1, n // 3)
        i2 = max(i1 + 1, (2 * n) // 3)
        h_start = max(s, float(dlg[0].get("start_sec") or s))
        h_end = min(e, float(dlg[i1 - 1].get("end_sec") or h_start))
        r_start = h_end
        r_end = min(e, float(dlg[i2 - 1].get("end_sec") or r_start))
        c_start = r_end
        c_end = e
        parts = [
            ("hook", h_start, h_end, "Hook (opening lines)"),
            ("rise", r_start, r_end, "Escalation"),
            ("cliffhanger", c_start, c_end, "Cliffhanger (exit line)"),
        ]
        for role, a, b_, lab in parts:
            if b_ <= a:
                continue
            segments.append(
                {
                    "index": len(segments) + 1,
                    "role": role,
                    "scene_id": g["scene_id"],
                    "start_sec": round(a, 2),
                    "end_sec": round(b_, 2),
                    "label": f"{lab} · {g['scene_id']}",
                }
            )
    elif d >= 18:
        t1 = s + d * 0.28
        t2 = s + d * 0.72
        for role, a, b_, lab in [
            ("hook", s, t1, "Hook setup"),
            ("rise", t1, t2, "Escalation"),
            ("cliffhanger", t2, e, "Cliffhanger pay-off"),
        ]:
            segments.append(
                {
                    "index": len(segments) + 1,
                    "role": role,
                    "scene_id": g["scene_id"],
                    "start_sec": round(a, 2),
                    "end_sec": round(b_, 2),
                    "label": f"{lab} · {g['scene_id']}",
                }
            )

    return segments


def why_it_works(promo: Dict[str, Any], hook: str, cliff: str, logline: str = "") -> str:
    """One editorial line — assignment requirement."""
    types = promo.get("promo_types") or []
    type_s = "/".join(types[:2]) if types else "dramatic"
    score = promo.get("overall_score")
    bits = []

    blob = f"{hook or ''} {cliff or ''} {promo.get('window_text') or ''}".lower()
    if any(k in blob for k in ("father", "mother", "daughter", "son", "duke")):
        bits.append("identity/lineage stakes land fast")
    if any(k in blob for k in ("betray", "wedding", "disown", "bridal", "altar")):
        bits.append("betrayal/power turn is instantly readable cold")
    if any(k in blob for k in ("love", "kiss", "protect", "don't die", "stay", "embrace")):
        bits.append("intimacy and danger collide")
    if any(k in blob for k in ("blood", "wound", "kill", "attack", "sword")):
        bits.append("physical peril raises binge urgency")
    if "?" in (hook or "") or "?" in (cliff or ""):
        bits.append("open question pulls the next click")
    if "!" in (hook or "") or "!" in (cliff or ""):
        bits.append("high-voltage delivery")

    if not bits:
        bits.append("clean hook→pressure→turn inside a tight window")

    # Keep to ~1–2 crisp clauses (assignment: one line)
    core = bits[0] if len(bits) == 1 else f"{bits[0]}; {bits[1]}"
    return f"{type_s.title()} beat ({score}/10): {core}."


def pick_champions(
    final_promos: List[Dict[str, Any]],
    episode_numbers: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """Best promo per episode by overall_score (then hook).

    Tie-break prefers more standalone-looking trigger text length and mid duration.
    """
    by_ep: Dict[int, List[Dict[str, Any]]] = {}
    for p in final_promos:
        ep = int(p.get("episode") or 0)
        by_ep.setdefault(ep, []).append(p)

    eps = episode_numbers or sorted(by_ep.keys())
    champs = []
    for ep in eps:
        cands = by_ep.get(ep) or []
        if not cands:
            continue

        def _key(x):
            dur = float(x.get("duration_sec") or 30)
            dur_bonus = 1.0 if 18 <= dur <= 50 else 0.0
            text_len = len((x.get("trigger_text") or "") + (x.get("window_text") or ""))
            return (
                float(x.get("overall_score") or 0),
                float(x.get("hook_strength") or 0),
                float(x.get("cliffhanger_strength") or 0),
                dur_bonus,
                min(text_len, 500) / 500.0,
            )

        cands = sorted(cands, key=_key, reverse=True)
        champs.append(cands[0])
    return champs


def enrich_champion(promo: Dict[str, Any], logline: str = "") -> Dict[str, Any]:
    ep = int(promo.get("episode") or 0)
    ep_data = _load_episode(ep)
    hook, cliff = extract_hook_and_cliff(promo, ep_data)
    segments = build_segments(promo, ep_data)
    row = dict(promo)
    row["hook"] = hook
    row["cliffhanger"] = cliff
    row["segments"] = segments
    row["why_it_works"] = why_it_works(promo, hook, cliff, logline)
    row["episode_logline"] = logline
    row["timecode"] = {
        "start_sec": round(float(promo.get("start_sec") or 0), 2),
        "end_sec": round(float(promo.get("end_sec") or 0), 2),
        "duration_sec": round(float(promo.get("duration_sec") or 0), 2),
        "start_tc": _sec_to_tc(float(promo.get("start_sec") or 0)),
        "end_tc": _sec_to_tc(float(promo.get("end_sec") or 0)),
    }
    return row


def _sec_to_tc(sec: float) -> str:
    sec = max(0.0, float(sec))
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    f = int(round((sec - int(sec)) * 1000))  # ms
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}.{f:03d}"
    return f"{m:02d}:{s:02d}.{f:03d}"


def _ensure_card_fields(r: Dict[str, Any], ll_map: Dict[int, str]) -> Dict[str, Any]:
    """Ensure hook/cliff/segments/timecode/post_why on a promo row."""
    ep = int(r.get("episode") or 0)
    if not r.get("hook") or not r.get("segments") or not r.get("timecode"):
        r = enrich_champion(r, r.get("episode_logline") or ll_map.get(ep, ""))
    if not r.get("hook"):
        r["hook"] = r.get("trigger_text") or ""
    if not r.get("cliffhanger"):
        r["cliffhanger"] = r.get("hook")
    if not r.get("timecode"):
        r["timecode"] = {
            "start_sec": round(float(r.get("start_sec") or 0), 2),
            "end_sec": round(float(r.get("end_sec") or 0), 2),
            "duration_sec": round(float(r.get("duration_sec") or 0), 2),
            "start_tc": _sec_to_tc(float(r.get("start_sec") or 0)),
            "end_tc": _sec_to_tc(float(r.get("end_sec") or 0)),
        }
    if not r.get("post_why"):
        r["post_why"] = posting_why(r)
    return r


def _pack_row(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "campaign_rank": r.get("campaign_rank") or r.get("post_rank"),
        "post_rank": r.get("post_rank") or r.get("campaign_rank"),
        "episode": r.get("episode"),
        "series_global_score": r.get("series_global_score", r.get("series_score")),
        "series_score": r.get("series_global_score", r.get("series_score")),
        "adjusted_series_score": r.get("adjusted_series_score"),
        "overall_score": r.get("overall_score"),
        "campaign_role": (r.get("series_breakdown") or {}).get("campaign_role"),
        "continuity_themes": r.get("continuity_themes")
        or (r.get("series_breakdown") or {}).get("continuity_themes"),
        "timecode": r.get("timecode"),
        "hook": r.get("hook"),
        "cliffhanger": r.get("cliffhanger"),
        "why_it_works": r.get("why_it_works"),
        "post_why": r.get("post_why"),
        "promo_types": r.get("promo_types"),
        "segments": r.get("segments"),
        "scene_ids": r.get("scene_ids"),
        "start_sec": r.get("start_sec"),
        "end_sec": r.get("end_sec"),
        "duration_sec": r.get("duration_sec"),
    }


def build_deliverable(
    mode_report: Dict[str, Any],
    mode_name: str = "hybrid",
    episode_numbers: Optional[List[int]] = None,
    top_n: Optional[int] = None,
    max_per_episode: int = 2,
    rebuild_continuity_map: bool = True,
    marketer_trim: bool = True,
    marketer_min_keep: int = 12,
    marketer_max_keep: int = 22,
    marketer_use_llm: bool = False,
) -> Dict[str, Any]:
    """Two-layer deliverable:

    A) Campaign pack — global rank over FULL hybrid pool (top-k/ep), N=20–30
       (or user top_n). Score ignores promo_types labels.
    B) Per-episode catalogue — best-in-ep for episode pages / assignment.
    """
    ctx = load_series_context()
    if rebuild_continuity_map:
        continuity = save_continuity_map()
    else:
        continuity = load_continuity_map()

    ll_map = {int(r["ep"]): r.get("logline") or "" for r in (ctx.get("loglines") or []) if "ep" in r}
    for row in continuity.get("loglines") or []:
        try:
            ll_map[int(row["ep"])] = row.get("logline") or ll_map.get(int(row["ep"]), "")
        except (KeyError, TypeError, ValueError):
            pass

    finals = mode_report.get("final_promos") or mode_report.get("selected_promos") or []
    eps = episode_numbers or mode_report.get("episodes") or sorted(
        {int(p.get("episode")) for p in finals}
    )
    eps = [int(e) for e in eps]

    # --- Layer A: global campaign pack from FULL pool ---
    campaign_meta = build_campaign_pack(
        finals,
        top_n=top_n,
        min_n=20,
        max_n=30,
        max_per_episode=max_per_episode,
        continuity=continuity,
        series_context=ctx,
        marketer_trim=False,  # single Marketer pass after enrich only
        marketer_min_keep=marketer_min_keep,
        marketer_max_keep=marketer_max_keep,
        marketer_use_llm=False,
    )
    pack_raw = campaign_meta.get("campaign_pack") or []
    campaign_meta["marketer"] = {
        "enabled": marketer_trim,
        "pre_marketer_n": len(pack_raw),
        "cut_list": [],
    }
    # Enrich first so Marketer sees real hooks/cliffs (not raw trigger stubs)
    pack_enriched_pre = []
    for r in pack_raw:
        pack_enriched_pre.append(_ensure_card_fields(dict(r), ll_map))

    # Re-run Marketer on enriched cards when trim enabled (final QA pass)
    if marketer_trim and pack_enriched_pre:
        from src.marketer_agent import run_marketer_agent
        m2 = run_marketer_agent(
            pack_enriched_pre,
            min_keep=marketer_min_keep,
            max_keep=marketer_max_keep,
            use_llm=marketer_use_llm,
            continuity_one_liner=str(continuity.get("series_one_liner") or ""),
        )
        pack_enriched_pre = m2.get("campaign_pack") or pack_enriched_pre
        # merge cut lists
        prev_cuts = (campaign_meta.get("marketer") or {}).get("cut_list") or []
        campaign_meta["marketer"] = {
            **(campaign_meta.get("marketer") or {}),
            "kept": m2.get("kept"),
            "cut_count": len(prev_cuts) + int(m2.get("cut_count") or 0),
            "protected_count": m2.get("protected_count"),
            "cut_list": prev_cuts + (m2.get("cut_list") or []),
            "pre_marketer_n": (campaign_meta.get("marketer") or {}).get("pre_marketer_n")
            or len(pack_raw),
            "final_pass": True,
            "marketer_note": m2.get("marketer_note"),
        }
        campaign_meta["top_n_after_marketer"] = len(pack_enriched_pre)

    pack_enriched = []
    for r in pack_enriched_pre:
        pr = _pack_row(r)
        pr["marketer_protected"] = bool(r.get("marketer_protected"))
        pr["marketer_decision"] = r.get("marketer_decision")
        pack_enriched.append(pr)

    # --- Layer B: per-episode champions (catalogue) ---
    champs_raw = pick_champions(finals, eps)
    enriched = []
    for p in champs_raw:
        ep = int(p.get("episode") or 0)
        enriched.append(enrich_champion(p, ll_map.get(ep, "")))

    # Rank champions for catalogue-only ordering (max 1/ep)
    ranked_champs = rank_series_champions(enriched, ctx)
    for r in ranked_champs:
        _ensure_card_fields(r, ll_map)

    # Map ep -> best campaign appearance (if any)
    camp_by_ep: Dict[int, Dict[str, Any]] = {}
    for r in pack_enriched:
        ep = int(r.get("episode") or 0)
        if ep not in camp_by_ep:
            camp_by_ep[ep] = r

    rank_by_ep = {int(r["episode"]): r for r in ranked_champs}
    by_ep = {int(p["episode"]): p for p in enriched}
    per_episode = []
    for ep in sorted(by_ep.keys()):
        base = by_ep[ep]
        r = rank_by_ep.get(ep, {})
        c = camp_by_ep.get(ep, {})
        per_episode.append(
            {
                "episode": ep,
                "logline": base.get("episode_logline") or ll_map.get(ep, ""),
                "catalogue_rank": r.get("post_rank"),
                "campaign_rank": c.get("campaign_rank"),
                "in_campaign_pack": bool(c),
                "series_score": r.get("series_score") or r.get("series_global_score"),
                "series_global_score": r.get("series_global_score", r.get("series_score")),
                "series_breakdown": r.get("series_breakdown"),
                "post_why": r.get("post_why"),
                "overall_score": base.get("overall_score"),
                "promo_types": base.get("promo_types"),
                "continuity_themes": r.get("continuity_themes")
                or (r.get("series_breakdown") or {}).get("continuity_themes"),
                "timecode": base.get("timecode") or r.get("timecode"),
                "segments": base.get("segments") or r.get("segments"),
                "hook": base.get("hook") or r.get("hook"),
                "cliffhanger": base.get("cliffhanger") or r.get("cliffhanger"),
                "why_it_works": base.get("why_it_works") or r.get("why_it_works"),
                "trigger_text": base.get("trigger_text"),
                "window_text": base.get("window_text"),
                "llm_rationale": base.get("llm_rationale"),
                "scene_ids": base.get("scene_ids"),
            }
        )

    # Champion catalogue posting order (legacy key)
    catalogue_order = [_pack_row(r) for r in ranked_champs]

    return {
        "mode": mode_name,
        "continuity_map": {
            "name": CONTINUITY_MAP_NAME,
            "path": "data/processed/series_continuity_map.json",
            "series_one_liner": continuity.get("series_one_liner"),
            "spine_themes": [
                {"id": t.get("id"), "label": t.get("label"), "weight": t.get("spine_weight")}
                for t in (continuity.get("spine_themes") or [])[:8]
            ],
            "principals": continuity.get("principals") or [],
            "episodes_indexed": continuity.get("episodes_indexed"),
        },
        "total_episodes_with_promo": len(per_episode),
        "missing_episodes": [e for e in eps if int(e) not in by_ep],
        "pool_size": campaign_meta.get("pool_size"),
        # Primary "post first" list — full-pool global rank
        "campaign_pack": pack_enriched,
        "campaign_meta": {
            "top_n": campaign_meta.get("top_n"),
            "top_n_after_marketer": campaign_meta.get("top_n_after_marketer"),
            "top_n_auto": campaign_meta.get("top_n_auto"),
            "top_n_rule": campaign_meta.get("top_n_rule"),
            "max_per_episode": campaign_meta.get("max_per_episode"),
            "type_mix": campaign_meta.get("type_mix"),
            "continuity_theme_mix": campaign_meta.get("continuity_theme_mix"),
            "episodes_represented": campaign_meta.get("episodes_represented"),
            "ranking_excludes_promo_types": True,
            "ranking_note": campaign_meta.get("ranking_note"),
            "marketer": campaign_meta.get("marketer") or {},
        },
        "marketer_cut_list": (campaign_meta.get("marketer") or {}).get("cut_list") or [],
        # Alias for older readers
        "series_posting_order": pack_enriched,
        "catalogue_posting_order": catalogue_order,
        "per_episode_best": per_episode,
        "ranking_method": {
            "continuity_map": (
                f"{CONTINUITY_MAP_NAME}: built from all episode loglines + beat text; "
                "spine themes, principals, arc phases. Not used as a type filter."
            ),
            "global_pool": (
                "ALL hybrid final promos (top-k per ep), not only 1/ep champions"
            ),
            "series_global_score": (
                "0.26*overall + 0.16*hook + 0.16*cliff + 0.08*emotional + "
                "0.06*narrative + 0.14*continuity_fit + 0.10*standalone_clarity + "
                "0.04*campaign_role + 0.04*duration_fit - 0.06*spoiler_risk. "
                "promo_types / classification labels are EXCLUDED from the score."
            ),
            "campaign_pack": (
                "Take top N by global score with soft diversity (type mix, theme mix, "
                f"ep spacing, max {max_per_episode}/ep). N user-set or auto in [20,30] "
                "via score floor + elbow + high-score richness."
            ),
            "marketer_agent": (
                "Marketer Agent trims weak tail (thin hooks, bad segments, low clarity) "
                "but PROTECTS top-12 / global>=7.85 / strong craft. Types never decide cut. "
                f"Keep window [{marketer_min_keep},{marketer_max_keep}]."
            ),
            "per_episode_catalogue": (
                "max overall_score (then hook, cliff, duration) among hybrid top-k — "
                "for episode pages / assignment 'best per ep'"
            ),
            "marketer_note": (
                "Classification labels stay on cards so marketers can experiment with "
                "all kinds; ranking never prefers one label over another."
            ),
        },
    }



def render_markdown(doc: Dict[str, Any]) -> str:
    def _esc(x: Any) -> str:
        return str(x or "").replace("|", "/").replace("\n", " ")

    lines: List[str] = []
    lines.append("# Find the Promos — Final Deliverable")
    lines.append("")
    lines.append(
        "> Per promo: **episode**, **ordered segment timestamps**, **hook**, "
        "**cliffhanger**, **why it works**. Campaign pack ranked with "
        f"**{CONTINUITY_MAP_NAME}** + global score (classification labels are tags only)."
    )
    lines.append("")
    lines.append(f"**Mode:** `{doc.get('mode')}`")
    lines.append(f"**Episodes covered:** {doc.get('total_episodes_with_promo')}")
    lines.append(f"**Global pool size:** {doc.get('pool_size')}")
    cm = doc.get("continuity_map") or {}
    meta = doc.get("campaign_meta") or {}
    lines.append(
        f"**Campaign pack N:** {meta.get('top_n')} "
        f"({'auto' if meta.get('top_n_auto') else 'user'}) — {meta.get('top_n_rule')}"
    )
    if doc.get("missing_episodes"):
        lines.append(f"**Missing:** {doc['missing_episodes']}")
    lines.append("")

    lines.append(f"## 0. {CONTINUITY_MAP_NAME}")
    lines.append("")
    lines.append(
        f"Whole-series context built from **all episode inputs** "
        f"({cm.get('episodes_indexed')} eps). Used for fit/clarity — "
        "**not** to force one promo type."
    )
    lines.append("")
    if cm.get("series_one_liner"):
        lines.append(f"> {cm.get('series_one_liner')}")
        lines.append("")
    if cm.get("spine_themes"):
        lines.append(
            "**Spine themes:** "
            + ", ".join(
                f"{t.get('label')} ({t.get('id')})" for t in cm["spine_themes"][:6]
            )
        )
        lines.append("")
    if cm.get("principals"):
        lines.append(
            "**Principals:** "
            + ", ".join(
                f"{p.get('name')}x{p.get('mentions')}" for p in cm["principals"][:8]
            )
        )
        lines.append("")
    lines.append(
        f"Artifact: `{cm.get('path') or 'data/processed/series_continuity_map.json'}`"
    )
    lines.append("")

    lines.append("## How ranking works")
    lines.append("")
    rm = doc.get("ranking_method") or {}
    for key in (
        "continuity_map",
        "global_pool",
        "series_global_score",
        "campaign_pack",
        "per_episode_catalogue",
        "marketer_note",
    ):
        if rm.get(key):
            lines.append(f"- **{key.replace('_', ' ').title()}:** {rm[key]}")
    lines.append("")
    if meta.get("type_mix"):
        lines.append(f"**Type mix in pack (tags only):** {meta.get('type_mix')}")
        lines.append("")
    if meta.get("continuity_theme_mix"):
        lines.append(f"**Continuity theme mix:** {meta.get('continuity_theme_mix')}")
        lines.append("")
    mk = meta.get("marketer") or {}
    if mk:
        lines.append(
            f"**Marketer Agent:** kept {mk.get('kept')} / pre {mk.get('pre_marketer_n')} "
            f"(cut {mk.get('cut_count')}, protected {mk.get('protected_count')})"
        )
        lines.append("")
    cuts = doc.get("marketer_cut_list") or []
    if cuts:
        lines.append("### Marketer cuts (removed from campaign pack)")
        lines.append("")
        for c in cuts:
            lines.append(
                f"- ep {c.get('episode')} old#{c.get('old_rank')} "
                f"g={c.get('series_global_score')}: {c.get('reason')} — "
                f"{(c.get('hook') or '')[:60]}"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## A. Campaign pack — post these first (global rank)")
    lines.append("")
    pack = doc.get("campaign_pack") or doc.get("series_posting_order") or []
    lines.append(
        "| Rank | Ep | Global | Role | Types (tag) | Themes | Start → End | Dur | Hook |"
    )
    lines.append(
        "|-----:|---:|-------:|------|-------------|--------|-------------|----:|------|"
    )
    for r in pack:
        tc = r.get("timecode") or {}
        hook = _esc(r.get("hook"))
        if len(hook) > 40:
            hook = hook[:37] + "…"
        themes = ",".join(r.get("continuity_themes") or [])[:28]
        types = ",".join(r.get("promo_types") or [])[:20]
        lines.append(
            f"| {r.get('campaign_rank') or r.get('post_rank')} | {r.get('episode')} | "
            f"{r.get('series_global_score', r.get('series_score'))} | "
            f"{r.get('campaign_role')} | {types} | {themes} | "
            f"{tc.get('start_tc', tc.get('start_sec'))} → "
            f"{tc.get('end_tc', tc.get('end_sec'))} | {tc.get('duration_sec')}s | {hook} |"
        )
    lines.append("")
    lines.append("### Campaign cards (detail)")
    lines.append("")
    for r in pack:
        tc = r.get("timecode") or {}
        rank = r.get("campaign_rank") or r.get("post_rank")
        lines.append(
            f"#### #{rank} · Episode {r.get('episode')} · "
            f"`{tc.get('start_tc')}` → `{tc.get('end_tc')}` ({tc.get('duration_sec')}s)"
        )
        lines.append("")
        lines.append(
            f"global=**{r.get('series_global_score', r.get('series_score'))}** · "
            f"ep_score={r.get('overall_score')} · role=*{r.get('campaign_role')}* · "
            f"tags={r.get('promo_types')} · spine={r.get('continuity_themes')}"
        )
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| **Hook** | {_esc(r.get('hook'))} |")
        lines.append(f"| **Cliffhanger** | {_esc(r.get('cliffhanger'))} |")
        lines.append(f"| **Why it works** | {_esc(r.get('why_it_works'))} |")
        lines.append(f"| **Why post here** | {_esc(r.get('post_why'))} |")
        lines.append("")
        lines.append("**Segments (in order):**")
        lines.append("")
        lines.append("| # | Role | Start (s) | End (s) | Label |")
        lines.append("|--:|------|----------:|--------:|-------|")
        for s in r.get("segments") or []:
            lines.append(
                f"| {s.get('index')} | {s.get('role')} | {s.get('start_sec')} | "
                f"{s.get('end_sec')} | {_esc(s.get('label'))} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## B. Best promo per episode (catalogue)")
    lines.append("")

    for p in doc.get("per_episode_best") or []:
        tc = p.get("timecode") or {}
        lines.append(f"### Episode {p.get('episode')}")
        lines.append("")
        if p.get("logline"):
            lines.append(f"*Logline:* {p.get('logline')}")
            lines.append("")
        in_pack = "yes" if p.get("in_campaign_pack") else "no"
        camp = f" (#{p.get('campaign_rank')})" if p.get("campaign_rank") else ""
        lines.append(
            f"**Cut:** `{tc.get('start_tc')}` → `{tc.get('end_tc')}` "
            f"({tc.get('duration_sec')}s) | "
            f"**In campaign pack:** {in_pack}{camp} | "
            f"**ep_score:** {p.get('overall_score')}/10 | "
            f"**types:** {p.get('promo_types')}"
        )
        lines.append("")
        lines.append(f"- **Hook:** {_esc(p.get('hook'))}")
        lines.append(f"- **Cliffhanger:** {_esc(p.get('cliffhanger'))}")
        lines.append(f"- **Why it works:** {_esc(p.get('why_it_works'))}")
        lines.append("")
        lines.append("| Seg | Role | Start (s) | End (s) | Label |")
        lines.append("|----:|------|----------:|--------:|-------|")
        for s in p.get("segments") or []:
            lines.append(
                f"| {s.get('index')} | {s.get('role')} | {s.get('start_sec')} | "
                f"{s.get('end_sec')} | {_esc(s.get('label'))} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## C. Editor summary")
    lines.append("")
    top = pack[:8]
    if top:
        lines.append("Lead the campaign with:")
        lines.append("")
        for i, r in enumerate(top, 1):
            lines.append(
                f"{i}. **Ep {r.get('episode')}** — {r.get('campaign_role')} — "
                f"global {r.get('series_global_score', r.get('series_score'))} — "
                f"{_esc(r.get('hook'))[:70]}"
            )
        lines.append("")
    lines.append(
        f"Ranking uses **{CONTINUITY_MAP_NAME}** + intrinsic quality + standalone "
        "clarity. **Promo classification labels never enter the score** — they stay "
        "on cards so marketers can A/B every kind. Pack size is user `--top-n` or "
        "auto 20–30 from score floor + elbow."
    )
    lines.append("")
    return "\n".join(lines)



def write_deliverable(
    mode_json_path: str,
    out_dir: str = "output/final",
    mode_name: str = "hybrid",
    episode_numbers: Optional[List[int]] = None,
    top_n: Optional[int] = None,
    max_per_episode: int = 2,
    marketer_trim: bool = True,
    marketer_min_keep: int = 12,
    marketer_max_keep: int = 22,
    marketer_use_llm: bool = False,
) -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    with open(mode_json_path, encoding="utf-8") as f:
        mode_report = json.load(f)

    doc = build_deliverable(
        mode_report,
        mode_name=mode_name,
        episode_numbers=episode_numbers or list(range(1, 51)),
        top_n=top_n,
        max_per_episode=max_per_episode,
        marketer_trim=marketer_trim,
        marketer_min_keep=marketer_min_keep,
        marketer_max_keep=marketer_max_keep,
        marketer_use_llm=marketer_use_llm,
    )
    json_path = os.path.join(out_dir, f"FINAL_PROMOS_{mode_name}.json")
    md_path = os.path.join(out_dir, f"FINAL_PROMOS_{mode_name}.md")
    csv_path = os.path.join(out_dir, f"FINAL_PROMOS_{mode_name}_campaign_pack.csv")
    # legacy alias
    csv_legacy = os.path.join(out_dir, f"FINAL_PROMOS_{mode_name}_posting_order.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(doc))

    import csv as _csv

    def _write_csv(path: str) -> None:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = _csv.writer(f)
            w.writerow(
                [
                    "campaign_rank",
                    "episode",
                    "series_global_score",
                    "campaign_role",
                    "continuity_themes",
                    "promo_types_tag",
                    "start_sec",
                    "end_sec",
                    "duration_sec",
                    "start_tc",
                    "end_tc",
                    "overall_score",
                    "hook",
                    "cliffhanger",
                    "why_it_works",
                    "post_why",
                ]
            )
            for r in doc.get("campaign_pack") or doc.get("series_posting_order") or []:
                tc = r.get("timecode") or {}
                w.writerow(
                    [
                        r.get("campaign_rank") or r.get("post_rank"),
                        r.get("episode"),
                        r.get("series_global_score", r.get("series_score")),
                        r.get("campaign_role"),
                        "|".join(r.get("continuity_themes") or []),
                        "|".join(r.get("promo_types") or []),
                        tc.get("start_sec"),
                        tc.get("end_sec"),
                        tc.get("duration_sec"),
                        tc.get("start_tc"),
                        tc.get("end_tc"),
                        r.get("overall_score"),
                        r.get("hook"),
                        r.get("cliffhanger"),
                        r.get("why_it_works"),
                        r.get("post_why"),
                    ]
                )

    _write_csv(csv_path)
    _write_csv(csv_legacy)

    # Slim continuity map copy next to deliverable
    cm_src = "data/processed/series_continuity_map.json"
    cm_dst = os.path.join(out_dir, "series_continuity_map.json")
    if os.path.exists(cm_src):
        import shutil

        shutil.copy2(cm_src, cm_dst)

    return {
        "json": json_path,
        "md": md_path,
        "csv": csv_path,
        "continuity_map": cm_dst if os.path.exists(cm_dst) else cm_src,
        "doc": doc,
    }
