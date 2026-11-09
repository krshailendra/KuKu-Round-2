"""Data + pipeline glue for the KuKu Promo Finder prototype UI."""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_FINAL = ROOT / "output" / "final"
OUTPUT_COMPARE = ROOT / "output" / "full_compare"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_RAW = ROOT / "data" / "raw_episodes"
UPLOADS = ROOT / "data" / "uploads"
JOBS: Dict[str, Dict[str, Any]] = {}
_LOCK = threading.RLock()

# In-memory active result (swapped when a job finishes or user loads a mode)
_STATE: Dict[str, Any] = {
    "mode": "hybrid",
    "doc": None,
    "episode_pool": [],  # enriched multi-promo pool for episode explorer
    "source_path": None,
    "loaded_at": None,
}


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_script_folders() -> List[Dict[str, Any]]:
    """Discover folders that look like episode script packs (fast, shallow)."""
    # Public deploy: do not advertise private assignment dataset paths even if present on disk.
    if os.getenv("DEMO_PUBLIC", "").strip().lower() in ("1", "true", "yes"):
        return []
    found: List[Dict[str, Any]] = []
    skip = {
        "node_modules",
        ".git",
        "__pycache__",
        "output",
        "src",
        "web",
        "evaluation",
        "docs",
        "venv",
        ".venv",
        "data",
    }
    candidates: List[Path] = [
        ROOT / "I Married a Broken Soldier. He was a Duke",
        DATA_RAW,
    ]
    try:
        if UPLOADS.is_dir():
            for sub in UPLOADS.iterdir():
                if sub.is_dir():
                    candidates.append(sub)
    except OSError:
        pass
    try:
        for p in ROOT.iterdir():
            if p.is_dir() and not p.name.startswith(".") and p.name.lower() not in skip:
                candidates.append(p)
    except OSError:
        pass

    seen = set()
    for folder in candidates:
        try:
            folder = folder.resolve()
        except OSError:
            continue
        key = str(folder).lower()
        if key in seen or not folder.is_dir():
            continue
        if folder.name.lower() in skip:
            continue
        try:
            txts = list(folder.glob("episode-*.txt")) or list(folder.glob("*.txt"))
        except OSError:
            continue
        if not txts:
            continue
        seen.add(key)
        found.append(
            {
                "path": str(folder),
                "name": folder.name,
                "script_count": len(txts),
                "sample": sorted(x.name for x in txts)[:3],
            }
        )
    found.sort(key=lambda x: (-x["script_count"], x["name"]))
    return found


def mode_options() -> List[Dict[str, str]]:
    return [
        {
            "id": "rule",
            "label": "Rule-based",
            "badge": None,
            "blurb": "Fast, offline, deterministic. Best for bulk harvest and CI.",
            "works_for": "Speed, reproducibility, no API keys, first-pass coverage across 50+ eps",
        },
        {
            "id": "hybrid",
            "label": "Hybrid",
            "badge": "Recommended",
            "blurb": "Rules + LLM scoring. Best balance of taste and cost.",
            "works_for": "Assignment default, production shortlist, Marketer pack",
        },
        {
            "id": "llm",
            "label": "LLM",
            "badge": None,
            "blurb": "Full model validation + scoring. Highest taste, slower/costlier.",
            "works_for": "Hero creative picks, editorial review, hard episodes rules miss",
        },
    ]


def feature_catalog() -> List[Dict[str, Any]]:
    """Every product capability exposed in the UI."""
    return [
        {
            "id": "parse",
            "name": "Screenplay parser",
            "desc": "Ingest episode .txt -> scenes, beats, dialogue, timestamps",
            "status": "live",
        },
        {
            "id": "candidates",
            "name": "Story-window candidates",
            "desc": "20-60s hook->cliff windows (usually 2-4 beats)",
            "status": "live",
        },
        {
            "id": "miniarc",
            "name": "Mini-arc validation",
            "desc": "Rule / Hybrid / LLM modes - does the cut stand alone?",
            "status": "live",
        },
        {
            "id": "score",
            "name": "Multi-criteria scoring",
            "desc": "Hook, cliff, emotion, clarity, narrative arc",
            "status": "live",
        },
        {
            "id": "types",
            "name": "Classification labels",
            "desc": "Tags only (not score drivers): emotional, cliffhanger, romantic...",
            "status": "live",
        },
        {
            "id": "continuity",
            "name": "Series Continuity Map",
            "desc": "Whole-show themes, characters, arcs for global ranking",
            "status": "live",
        },
        {
            "id": "global",
            "name": "Series global ranker",
            "desc": "Post-first order over the full promo pool",
            "status": "live",
        },
        {
            "id": "diversity",
            "name": "Campaign diversity pack",
            "desc": "Role mix + max-per-episode so the pack is not one-note",
            "status": "live",
        },
        {
            "id": "marketer",
            "name": "Marketer Agent",
            "desc": "Protect strong promos; cut weak tail / thin hooks",
            "status": "live",
        },
        {
            "id": "cards",
            "name": "Assignment cards",
            "desc": "Episode, ordered segment times, hook, cliff, why-it-works",
            "status": "live",
        },
        {
            "id": "episode_topn",
            "name": "Episode explorer",
            "desc": "Top 2 / 3 / 5 per episode + filter by label",
            "status": "live",
        },
        {
            "id": "export",
            "name": "Excel export",
            "desc": "Problem-statement Excel: episode, segments, hook, cliff, why",
            "status": "live",
        },
    ]


def _default_paths_for_mode(mode: str) -> Tuple[Optional[Path], Optional[Path]]:
    final = OUTPUT_FINAL / f"FINAL_PROMOS_{mode}.json"
    pool = OUTPUT_COMPARE / f"promos_{mode}_top5.json"
    if not final.exists():
        # fall back hybrid final
        alt = OUTPUT_FINAL / "FINAL_PROMOS_hybrid.json"
        final = alt if alt.exists() else None
    if not pool.exists():
        altp = OUTPUT_COMPARE / "promos_hybrid_top5.json"
        pool = altp if altp.exists() else None
    return final, pool


def _is_placeholder_why(text: Any) -> bool:
    s = (str(text) if text is not None else "").strip().lower()
    if not s:
        return True
    return s.startswith("rule-based score") or s.startswith("rule based score")


def _enrich_promo(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure hook / cliff / editorial why / segments exist.

    Harvest rows (promos_*_top5) often only have scores + window_text and a
    placeholder llm_rationale like "Rule-based score=7.2/10". Campaign pack
    rows already went through enrich_champion. Episode explorer must match pack.
    """
    p = dict(raw)
    hook_ok = bool(str(p.get("hook") or "").strip())
    cliff_ok = bool(str(p.get("cliffhanger") or p.get("cliff") or "").strip())
    segs_ok = bool(p.get("segments") or p.get("ordered_segments"))
    why_raw = p.get("why_it_works") or p.get("why") or p.get("llm_rationale") or ""
    why_ok = bool(str(why_raw).strip()) and not _is_placeholder_why(why_raw)

    if hook_ok and cliff_ok and segs_ok and why_ok:
        return _normalize_promo(p)

    if _is_placeholder_why(p.get("why_it_works")):
        p["why_it_works"] = ""

    try:
        from src.final_deliverable import enrich_champion  # type: ignore

        enriched = enrich_champion(p, p.get("episode_logline") or p.get("logline") or "")
        if isinstance(enriched, dict):
            for k, v in enriched.items():
                if k in ("hook", "cliffhanger", "why_it_works"):
                    cur = str(p.get(k) or "").strip()
                    if (not cur or _is_placeholder_why(cur)) and v:
                        p[k] = v
                elif k in ("segments", "ordered_segments", "timecode"):
                    if not p.get(k) and v:
                        p[k] = v
                else:
                    p.setdefault(k, v)
            if enriched.get("segments") and not p.get("ordered_segments"):
                p["ordered_segments"] = enriched["segments"]
            if enriched.get("why_it_works") and (
                not str(p.get("why_it_works") or "").strip()
                or _is_placeholder_why(p.get("why_it_works"))
            ):
                p["why_it_works"] = enriched["why_it_works"]
    except Exception as e:
        print(f"[web] enrich_promo fallback: {e}")

    if not str(p.get("hook") or "").strip():
        p["hook"] = (
            p.get("hook_text")
            or p.get("opening_line")
            or p.get("trigger_text")
            or p.get("logline")
            or ""
        )
    if not str(p.get("cliffhanger") or "").strip():
        p["cliffhanger"] = (
            p.get("cliff")
            or p.get("exit_line")
            or p.get("closing_line")
            or p.get("hook")
            or ""
        )
    if not p.get("segments"):
        p["segments"] = p.get("ordered_segments") or []
    if not p.get("ordered_segments"):
        p["ordered_segments"] = p.get("segments") or []
    if not str(p.get("why_it_works") or "").strip() or _is_placeholder_why(p.get("why_it_works")):
        bits = []
        types = p.get("promo_types") or p.get("labels") or []
        if isinstance(types, list) and types:
            bits.append("/".join(str(t).title() for t in types[:2]) + " beat")
        score = p.get("overall_score") or p.get("series_global_score")
        try:
            if score is not None:
                bits.append(f"({float(score):.2f}/10)")
        except Exception:
            pass
        mode = (p.get("pipeline_mode") or p.get("mode") or _STATE.get("mode") or "hybrid").lower()
        if mode == "hybrid":
            bits.append("hybrid pipeline (rule screen + selective LLM)")
        elif mode == "llm":
            bits.append("LLM-scored mini-arc")
        else:
            bits.append("rule-scored mini-arc")
        p["why_it_works"] = ": ".join(bits) if bits else "Stand-alone mini-arc with a clear exit beat."

    p.setdefault("pipeline_mode", p.get("mode") or _STATE.get("mode") or "hybrid")
    if p.get("mini_arc_mode") and not p.get("score_source"):
        p["score_source"] = str(p.get("mini_arc_mode"))
    return _normalize_promo(p)



def _sec_to_tc(sec: float) -> str:
    try:
        sec = float(sec)
    except (TypeError, ValueError):
        return "00:00.000"
    m = int(sec // 60)
    s = sec - m * 60
    return f"{m:02d}:{s:06.3f}"


def _normalize_promo(p: Dict[str, Any]) -> Dict[str, Any]:
    types = p.get("promo_types") or p.get("types") or p.get("labels") or []
    if isinstance(types, str):
        types = [t.strip() for t in types.split(",") if t.strip()]
    types = [str(t) for t in types]

    segs = p.get("ordered_segments") or p.get("segments") or []
    norm_segs = []
    for i, s in enumerate(segs):
        if not isinstance(s, dict):
            continue
        st = float(s.get("start_sec") if s.get("start_sec") is not None else p.get("start_sec") or 0)
        en = float(s.get("end_sec") if s.get("end_sec") is not None else p.get("end_sec") or st)
        norm_segs.append(
            {
                "index": s.get("index") or (i + 1),
                "role": s.get("role") or "beat",
                "scene_id": s.get("scene_id"),
                "start_sec": st,
                "end_sec": en,
                "start_tc": s.get("start_tc") or _sec_to_tc(st),
                "end_tc": s.get("end_tc") or _sec_to_tc(en),
                "label": s.get("label") or s.get("role") or f"Segment {i+1}",
                "dialogue_preview": s.get("dialogue_preview") or s.get("text") or "",
            }
        )
    if not norm_segs:
        st = float(p.get("start_sec") or 0)
        en = float(p.get("end_sec") or st)
        norm_segs = [
            {
                "index": 1,
                "role": "full_window",
                "start_sec": st,
                "end_sec": en,
                "start_tc": p.get("start_tc") or _sec_to_tc(st),
                "end_tc": p.get("end_tc") or _sec_to_tc(en),
                "label": "Full window",
                "dialogue_preview": "",
            }
        ]

    tc = p.get("timecode") or {}
    start_tc = tc.get("start_tc") or p.get("start_tc") or norm_segs[0]["start_tc"]
    end_tc = tc.get("end_tc") or p.get("end_tc") or norm_segs[-1]["end_tc"]

    return {
        "campaign_rank": p.get("campaign_rank") or p.get("post_rank"),
        "post_rank": p.get("post_rank") or p.get("campaign_rank"),
        "episode": int(p.get("episode") or 0),
        "series_global_score": p.get("series_global_score", p.get("series_score")),
        "overall_score": p.get("overall_score") or p.get("final_score") or p.get("score"),
        "campaign_role": p.get("campaign_role") or p.get("role") or "",
        "continuity_themes": p.get("continuity_themes") or p.get("themes") or [],
        "promo_types": types,
        "labels": types,  # alias for UI
        "start_sec": float(p.get("start_sec") or norm_segs[0]["start_sec"]),
        "end_sec": float(p.get("end_sec") or norm_segs[-1]["end_sec"]),
        "duration_sec": p.get("duration_sec")
        or round(
            float(p.get("end_sec") or 0) - float(p.get("start_sec") or 0),
            2,
        ),
        "start_tc": start_tc,
        "end_tc": end_tc,
        "hook": p.get("hook") or "",
        "cliffhanger": p.get("cliffhanger") or p.get("cliff") or "",
        "why_it_works": ("" if _is_placeholder_why(p.get("why_it_works") or p.get("why") or "") else (p.get("why_it_works") or p.get("why") or "")),
        "post_why": p.get("post_why") or "",
        "pipeline_mode": p.get("pipeline_mode") or p.get("mode") or _STATE.get("mode") or "hybrid",
        "score_source": p.get("score_source") or p.get("mini_arc_mode") or "",
        "mini_arc_mode": p.get("mini_arc_mode") or "",
        "segments": norm_segs,
        "ordered_segments": norm_segs,
        "scene_ids": p.get("scene_ids") or [],
        "marketer_protected": bool(p.get("marketer_protected")),
        "marketer_decision": p.get("marketer_decision") or "",
        "logline": p.get("logline") or "",
        "id": p.get("id") or p.get("promo_id") or "",
        "raw_scores": {
            k: p.get(k)
            for k in (
                "hook_strength",
                "cliffhanger_strength",
                "emotional_peak",
                "narrative_clarity",
                "standalone_score",
            )
            if p.get(k) is not None
        },
    }


def load_mode(mode: str = "hybrid", force_enrich_pool: bool = False) -> Dict[str, Any]:
    mode = (mode or "hybrid").lower()
    if mode not in ("rule", "hybrid", "llm"):
        mode = "hybrid"

    final_path, pool_path = _default_paths_for_mode(mode)
    if final_path and final_path.exists():
        doc = _read_json(final_path)
    else:
        doc = {
            "mode": mode,
            "campaign_pack": [],
            "per_episode_best": [],
            "series_posting_order": [],
            "marketer_cut_list": [],
            "continuity_map": {},
            "ranking_method": {},
            "total_episodes_with_promo": 0,
        }

    # Normalize campaign pack (already has hook/cliff/why in FINAL json)
    pack = [_normalize_promo(x) for x in (doc.get("campaign_pack") or [])]
    doc["campaign_pack"] = pack
    if doc.get("per_episode_best"):
        doc["per_episode_best"] = [_normalize_promo(x) for x in doc["per_episode_best"]]
    if doc.get("series_posting_order"):
        doc["series_posting_order"] = [
            _normalize_promo(x) if isinstance(x, dict) and ("episode" in x or "hook" in x) else x
            for x in doc["series_posting_order"]
        ]

    # Episode pool from top5 harvest — default: light normalize only (fast)
    pool: List[Dict[str, Any]] = []
    if pool_path and pool_path.exists():
        raw_pool = _read_json(pool_path)
        finals = raw_pool.get("final_promos") or raw_pool.get("promos") or []
        for item in finals:
            if force_enrich_pool:
                try:
                    pool.append(_enrich_promo(item))
                except Exception:
                    pool.append(_normalize_promo(item))
            else:
                pool.append(_normalize_promo(item))
    else:
        seen = set()
        for x in pack + (doc.get("per_episode_best") or []):
            key = (x.get("episode"), x.get("start_sec"), x.get("end_sec"))
            if key in seen:
                continue
            seen.add(key)
            pool.append(x)

    # Overlay hook/cliff/why/segments from FINAL pack + per-ep best (no slow re-parse)
    overlay: Dict[Tuple[int, float, float], Dict[str, Any]] = {}
    for src in pack + list(doc.get("per_episode_best") or []):
        try:
            key = (
                int(src.get("episode") or 0),
                round(float(src.get("start_sec") or 0), 1),
                round(float(src.get("end_sec") or 0), 1),
            )
        except (TypeError, ValueError):
            continue
        overlay[key] = src
    for i, p in enumerate(pool):
        try:
            key = (
                int(p.get("episode") or 0),
                round(float(p.get("start_sec") or 0), 1),
                round(float(p.get("end_sec") or 0), 1),
            )
        except (TypeError, ValueError):
            continue
        o = overlay.get(key)
        if not o:
            continue
        for fld in ("hook", "cliffhanger", "why_it_works", "segments", "post_why", "campaign_role"):
            if o.get(fld) and not p.get(fld):
                p[fld] = o[fld]
        if o.get("series_global_score") is not None and p.get("series_global_score") is None:
            p["series_global_score"] = o["series_global_score"]
        pool[i] = p

    # Ensure pool at least contains fully-carded pack + per-ep best
    seen_keys = set()
    for p in pool:
        try:
            seen_keys.add(
                (
                    int(p.get("episode") or 0),
                    round(float(p.get("start_sec") or 0), 1),
                    round(float(p.get("end_sec") or 0), 1),
                )
            )
        except (TypeError, ValueError):
            pass
    for src in pack + list(doc.get("per_episode_best") or []):
        try:
            key = (
                int(src.get("episode") or 0),
                round(float(src.get("start_sec") or 0), 1),
                round(float(src.get("end_sec") or 0), 1),
            )
        except (TypeError, ValueError):
            continue
        if key not in seen_keys:
            pool.append(src)
            seen_keys.add(key)

    with _LOCK:
        _STATE["mode"] = mode
        _STATE["doc"] = doc
        _STATE["episode_pool"] = pool
        _STATE["source_path"] = str(final_path) if final_path else None
        _STATE["loaded_at"] = datetime.utcnow().isoformat() + "Z"

    return snapshot()


def load_full_continuity_map(doc: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Prefer on-disk Series Continuity Map; fall back to slim embed in FINAL json."""
    doc = doc if doc is not None else (_STATE.get("doc") or {})
    slim = doc.get("continuity_map") or {}
    candidates: List[Path] = [
        ROOT / "output" / "final" / "series_continuity_map.json",
        DATA_PROCESSED / "series_continuity_map.json",
    ]
    # Active project output (if any)
    try:
        pid = (_STATE.get("project_id") or "").strip()
        if pid:
            candidates.insert(
                0, _project_dir(pid) / "output" / "series_continuity_map.json"
            )
    except Exception:
        pass
    path_s = slim.get("path") if isinstance(slim, dict) else None
    if path_s:
        p = Path(path_s)
        if not p.is_absolute():
            p = ROOT / p
        candidates.insert(0, p)
    for path in candidates:
        try:
            if path.is_file():
                full = _read_json(path)
                if isinstance(full, dict) and full:
                    full = dict(full)
                    full["_source_file"] = str(path)
                    # keep slim fields if full missing one-liner
                    if not full.get("series_one_liner") and slim.get("series_one_liner"):
                        full["series_one_liner"] = slim["series_one_liner"]
                    return full
        except Exception:
            continue
    return dict(slim) if isinstance(slim, dict) else {}


def marketer_payload(doc: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Human-readable marketer QA summary for the UI."""
    doc = doc if doc is not None else (_STATE.get("doc") or {})
    pack = doc.get("campaign_pack") or []
    meta = doc.get("campaign_meta") or {}
    mk = meta.get("marketer") if isinstance(meta.get("marketer"), dict) else {}
    cuts = (
        doc.get("marketer_cut_list")
        or mk.get("cut_list")
        or []
    )
    protected = mk.get("protected_count")
    if protected is None:
        protected = sum(1 for p in pack if p.get("marketer_protected"))
    kept = mk.get("kept") if mk.get("kept") is not None else len(pack)
    cut_n = mk.get("cut_count") if mk.get("cut_count") is not None else len(cuts)
    pre = mk.get("pre_marketer_n") or meta.get("top_n") or (int(kept) + int(cut_n))
    note = (
        mk.get("marketer_note")
        or mk.get("note")
        or "Protect top slots / high global score; cut thin hooks and muddy segments."
    )
    summary = (
        mk.get("summary")
        or meta.get("marketer_summary")
        or (
            "Marketer reviewed ~%s ranked candidates: protected %s hero posts, "
            "cut %s weak-tail clips, kept %s for the posting pack. "
            "Labels never decide keep/cut — craft, hook strength, segment clarity do."
            % (pre, protected, cut_n, kept)
        )
    )
    return {
        "summary": summary,
        "cut_count": cut_n,
        "protected_count": protected,
        "kept_count": kept,
        "pack_size": len(pack) or kept,
        "pre_marketer_n": pre,
        "cut_list": cuts,
        "max_per_episode": meta.get("max_per_episode"),
        "top_n_rule": meta.get("top_n_rule"),
        "note": note,
    }


def snapshot() -> Dict[str, Any]:
    with _LOCK:
        doc = _STATE.get("doc") or {}
        pack = doc.get("campaign_pack") or []
        pool = _STATE.get("episode_pool") or []
        labels = Counter()
        roles = Counter()
        for p in pack:
            for t in p.get("promo_types") or []:
                labels[t] += 1
            if p.get("campaign_role"):
                roles[p["campaign_role"]] += 1
        for p in pool:
            for t in p.get("promo_types") or []:
                labels[t] += 1

        mk_payload = marketer_payload(doc)
        cont = load_full_continuity_map(doc)

        return {
            "mode": _STATE.get("mode"),
            "loaded_at": _STATE.get("loaded_at"),
            "source_path": _STATE.get("source_path"),
            "total_campaign": len(pack),
            "total_pool": len(pool),
            "total_episodes_with_promo": doc.get("total_episodes_with_promo")
            or len(doc.get("per_episode_best") or []),
            "label_counts": dict(labels.most_common()),
            "role_counts": dict(roles.most_common()),
            "continuity_map": cont,
            "ranking_method": doc.get("ranking_method") or {},
            "campaign_meta": doc.get("campaign_meta") or {},
            "marketer": mk_payload,
            "features": feature_catalog(),
            "modes": mode_options(),
        }


def get_campaign_pack() -> List[Dict[str, Any]]:
    with _LOCK:
        doc = _STATE.get("doc") or {}
        pack = list(doc.get("campaign_pack") or [])
        if pack:
            return pack
    # Fallback: try active project disk results
    try:
        pid = get_active_project_id()
        if pid and load_project_results(pid):
            with _LOCK:
                return list((_STATE.get("doc") or {}).get("campaign_pack") or [])
    except Exception:
        pass
    return []


def get_posting_order() -> List[Dict[str, Any]]:
    with _LOCK:
        doc = _STATE.get("doc") or {}
        order = doc.get("series_posting_order")
        if order:
            out = []
            for i, x in enumerate(order):
                if isinstance(x, dict):
                    n = _normalize_promo(x) if "episode" in x else dict(x)
                    n.setdefault("post_rank", i + 1)
                    out.append(n)
            return out
        return list(doc.get("campaign_pack") or [])


def get_per_episode_best() -> List[Dict[str, Any]]:
    with _LOCK:
        doc = _STATE.get("doc") or {}
        return list(doc.get("per_episode_best") or [])


def _promo_dedupe_key(p: Dict[str, Any]) -> Tuple[Any, ...]:
    """Stable identity for promo deduplication across sources."""
    ep = int(p.get("episode") or 0)
    pid = str(p.get("id") or p.get("promo_id") or "").strip()
    if pid:
        return ("id", ep, pid)
    st_tc = str(p.get("start_tc") or "").strip()
    en_tc = str(p.get("end_tc") or "").strip()
    if st_tc or en_tc:
        return ("tc", ep, st_tc, en_tc)
    st = round(float(p.get("start_sec") or 0), 2)
    en = round(float(p.get("end_sec") or 0), 2)
    if st or en:
        return ("sec", ep, st, en)
    logline = str(p.get("logline") or p.get("hook") or "").strip()[:120].lower()
    if logline:
        return ("log", ep, logline)
    return ("obj", ep, id(p))


def _ensure_promo_fields(raw: Dict[str, Any], default_ep: Optional[int] = None) -> Dict[str, Any]:
    """Lightweight field fill when full normalize is not needed."""
    p = dict(raw)
    if default_ep is not None and not p.get("episode"):
        p["episode"] = default_ep
    p.setdefault("hook", p.get("hook_text") or p.get("logline") or "")
    p.setdefault("cliffhanger", p.get("cliff") or p.get("exit_text") or "")
    _why = p.get("why") or p.get("llm_rationale") or ""
    if _is_placeholder_why(_why):
        _why = ""
    p.setdefault("why_it_works", _why)
    p.setdefault("promo_types", p.get("labels") or p.get("types") or [])
    if not isinstance(p.get("promo_types"), list):
        p["promo_types"] = [str(p.get("promo_types"))]
    segs = p.get("ordered_segments") or p.get("segments") or []
    p["segments"] = segs if isinstance(segs, list) else []
    p.setdefault("ordered_segments", p["segments"])
    scores = p.get("scores") if isinstance(p.get("scores"), dict) else {}
    if p.get("series_global_score") is None and scores.get("series_global_score") is not None:
        p["series_global_score"] = scores.get("series_global_score")
    if p.get("overall_score") is None and scores.get("overall_score") is not None:
        p["overall_score"] = scores.get("overall_score")
    return p


def _iter_promo_lists_from_obj(obj: Any, default_ep: Optional[int] = None) -> List[Dict[str, Any]]:
    """Extract promo dicts from heterogeneous harvest / result shapes."""
    out: List[Dict[str, Any]] = []
    if obj is None:
        return out

    def _from_container(container: Any, ep_hint: Optional[int] = None) -> None:
        if isinstance(container, list):
            for item in container:
                if not isinstance(item, dict):
                    continue
                nested = None
                for k in (
                    "promos",
                    "top_promos",
                    "top_k_promos",
                    "selected_promos",
                    "final_promos",
                    "candidates",
                    "selected",
                    "results",
                ):
                    if isinstance(item.get(k), list):
                        nested = item.get(k)
                        break
                if nested is not None and (
                    item.get("episode") is not None or item.get("episode_number") is not None
                ):
                    try:
                        ep_n = int(item.get("episode") or item.get("episode_number") or ep_hint or 0)
                    except Exception:
                        ep_n = ep_hint or 0
                    for sub in nested:
                        if isinstance(sub, dict):
                            out.append(_ensure_promo_fields(sub, ep_n or None))
                else:
                    out.append(_ensure_promo_fields(item, ep_hint))
        elif isinstance(container, dict):
            if any(k in container for k in ("hook", "logline", "start_sec", "segments", "promo_types")):
                out.append(_ensure_promo_fields(container, ep_hint))

    if isinstance(obj, list):
        _from_container(obj, default_ep)
        return out

    if not isinstance(obj, dict):
        return out

    _LIST_KEYS = (
        "selected_promos",
        "final_promos",
        "promos",
        "top_promos",
        "top_k_promos",
        "candidates",
        "selected",
        "results",
    )
    for k in _LIST_KEYS:
        if isinstance(obj.get(k), list) and obj.get(k):
            _from_container(obj.get(k), default_ep)

    eps = obj.get("episodes")
    if isinstance(eps, list) and eps and isinstance(eps[0], dict):
        _from_container(eps, default_ep)
    elif isinstance(eps, dict):
        for ek, ev in eps.items():
            try:
                ep_n = int(ek)
            except Exception:
                ep_n = default_ep
            if isinstance(ev, list):
                _from_container(ev, ep_n)
            elif isinstance(ev, dict):
                grabbed = False
                for pk in _LIST_KEYS:
                    if isinstance(ev.get(pk), list):
                        _from_container(ev.get(pk), ep_n)
                        grabbed = True
                if not grabbed:
                    _from_container(ev, ep_n)

    for map_key in ("per_episode", "by_episode", "episode_promos", "results_by_episode", "per_episode_promos"):
        pe = obj.get(map_key)
        if not isinstance(pe, dict):
            continue
        for ek, ev in pe.items():
            try:
                ep_n = int(ek)
            except Exception:
                ep_n = default_ep
            if isinstance(ev, list):
                _from_container(ev, ep_n)
            elif isinstance(ev, dict):
                grabbed = False
                for pk in _LIST_KEYS:
                    if isinstance(ev.get(pk), list):
                        _from_container(ev.get(pk), ep_n)
                        grabbed = True
                if not grabbed and any(
                    k in ev for k in ("hook", "logline", "start_sec", "segments", "promo_types")
                ):
                    out.append(_ensure_promo_fields(ev, ep_n))

    # dict keyed directly by episode number (avoid mistaking FINAL meta docs)
    sample_keys = list(obj.keys())[: min(8, len(obj))]
    looks_ep_keyed = bool(sample_keys) and all(
        str(k).isdigit() or isinstance(k, int) for k in sample_keys
    )
    meta_markers = (
        "selected_promos",
        "final_promos",
        "campaign_pack",
        "per_episode_best",
        "mini_arc_mode",
        "scoring_mode",
        "ranking_method",
        "meta",
    )
    if looks_ep_keyed and not any(k in obj for k in meta_markers):
        for ek, ev in obj.items():
            try:
                ep_n = int(ek)
            except Exception:
                continue
            if isinstance(ev, list):
                _from_container(ev, ep_n)
            elif isinstance(ev, dict):
                grabbed = False
                for pk in _LIST_KEYS:
                    if isinstance(ev.get(pk), list):
                        _from_container(ev.get(pk), ep_n)
                        grabbed = True
                if not grabbed:
                    _from_container(ev, ep_n)

    return out


def _build_episode_pool_from_project(
    project_id: str, doc: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Merge campaign_pack + per_episode_best + harvest promos_*.json into one
    normalized, deduplicated promo pool sorted by episode then score desc.
    """
    doc = doc if isinstance(doc, dict) else {}
    raw_items: List[Dict[str, Any]] = []

    for p in doc.get("campaign_pack") or []:
        if isinstance(p, dict):
            raw_items.append(dict(p))
    for p in doc.get("per_episode_best") or []:
        if isinstance(p, dict):
            raw_items.append(dict(p))
    for k in ("selected_promos", "final_promos", "promos", "results"):
        for p in doc.get(k) or []:
            if isinstance(p, dict):
                raw_items.append(dict(p))

    try:
        out_dir = _project_output(project_id)
    except Exception:
        out_dir = Path()
    if out_dir.is_dir():
        harvest_paths = sorted(out_dir.glob("promos_*.json"))
        for alt in ("harvest_promos.json", "episode_promos.json", "all_promos.json"):
            ap = out_dir / alt
            if ap.exists() and ap not in harvest_paths:
                harvest_paths.append(ap)
        for hp in harvest_paths:
            try:
                payload = json.loads(hp.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[web] harvest read failed {hp}: {e}")
                continue
            before = len(raw_items)
            parsed = _iter_promo_lists_from_obj(payload)
            raw_items.extend(parsed)
            got = len(raw_items) - before
            if got == 0:
                keys = list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
                print(f"[web] harvest parse empty {hp.name}: keys={keys}")
            else:
                print(f"[web] harvest {hp.name}: +{got} promos")

    seen: set = set()
    pool: List[Dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        try:
            p = _enrich_promo(raw)
        except Exception:
            try:
                p = _normalize_promo(raw)
            except Exception:
                p = _ensure_promo_fields(raw)
        if not isinstance(p, dict):
            continue
        ep = int(p.get("episode") or 0)
        if ep <= 0:
            continue
        p.setdefault("hook", "")
        p.setdefault("cliffhanger", "")
        if _is_placeholder_why(p.get("why_it_works")):
            p["why_it_works"] = ""
        p.setdefault("why_it_works", "")
        p.setdefault("promo_types", [])
        p.setdefault("segments", p.get("ordered_segments") or [])
        p.setdefault("ordered_segments", p.get("segments") or [])
        if not isinstance(p.get("scores"), dict):
            p["scores"] = {
                "series_global_score": p.get("series_global_score"),
                "overall_score": p.get("overall_score"),
            }
        key = _promo_dedupe_key(p)
        if key in seen:
            continue
        seen.add(key)
        pool.append(p)

    def _score_of(x: Dict[str, Any]) -> float:
        try:
            if x.get("series_global_score") is not None:
                return float(x.get("series_global_score") or 0)
            if x.get("overall_score") is not None:
                return float(x.get("overall_score") or 0)
            sc = x.get("scores") if isinstance(x.get("scores"), dict) else {}
            return float(sc.get("series_global_score") or sc.get("overall_score") or 0)
        except Exception:
            return 0.0

    pool.sort(key=lambda x: (int(x.get("episode") or 0), -_score_of(x)))
    return pool


def get_episode_promos(
    top_n: int = 5,
    label: Optional[str] = None,
    episode: Optional[int] = None,
) -> Dict[str, Any]:
    """Full-series episode explorer (harvest + PEB + campaign), not campaign-only."""
    top_n = max(1, min(int(top_n or 5), 15))
    label_f = (label or "").strip().lower() or None
    try:
        ep_f = int(episode) if episode not in (None, "", 0, "0") else None
    except Exception:
        ep_f = None

    def _unique_eps(rows):
        s = set()
        for p in rows or []:
            if not isinstance(p, dict):
                continue
            try:
                e = int(p.get("episode") or 0)
            except Exception:
                e = 0
            if e > 0:
                s.add(e)
        return s

    with _LOCK:
        pool = list(_STATE.get("episode_pool") or [])
        doc = dict(_STATE.get("doc") or {})
        pid = _STATE.get("project_id") or get_active_project_id()

    # If no doc, try load active project
    if (not doc or not (doc.get("campaign_pack") or doc.get("per_episode_best"))) and pid:
        try:
            load_project_results(pid)
            with _LOCK:
                pool = list(_STATE.get("episode_pool") or [])
                doc = dict(_STATE.get("doc") or {})
        except Exception as e:
            print("[web] load for episodes failed:", e)

    peb = list(doc.get("per_episode_best") or [])
    pack = list(doc.get("campaign_pack") or [])
    need = _unique_eps(peb) | _unique_eps(pack)
    have = _unique_eps(pool)

    should_rebuild = (
        not pool
        or (need and not need.issubset(have))
        or (pid and len(have) < max(10, len(need)))
    )
    if should_rebuild:
        rebuilt = []
        try:
            if pid:
                rebuilt = _build_episode_pool_from_project(pid, doc) or []
        except Exception as e:
            print("[web] rebuild pool failed:", e)
        if not rebuilt:
            for x in pack + peb:
                if isinstance(x, dict):
                    rebuilt.append(dict(x))
        if rebuilt:
            pool = rebuilt
            with _LOCK:
                _STATE["episode_pool"] = list(rebuilt)
            print(f"[web] episode pool: {len(pool)} promos / {len(_unique_eps(pool))} eps")

    # normalize + group
    by_ep = {}
    label_counts = {}
    for raw in pool:
        if not isinstance(raw, dict):
            continue
        try:
            # Re-enrich if hook/why still missing (handles stale in-memory pool)
            need = (not str(raw.get("hook") or "").strip()) or _is_placeholder_why(
                raw.get("why_it_works") or raw.get("llm_rationale") or ""
            )
            if need:
                p = _enrich_promo(dict(raw))
            else:
                p = _normalize_promo(dict(raw)) if "episode" in raw else dict(raw)
        except Exception:
            try:
                p = _normalize_promo(dict(raw))
            except Exception:
                p = dict(raw)
        try:
            ep_n = int(p.get("episode") or 0)
        except Exception:
            ep_n = 0
        if ep_n <= 0:
            continue
        if ep_f is not None and ep_n != ep_f:
            continue
        labels = p.get("promo_types") or p.get("labels") or []
        if not isinstance(labels, list):
            labels = [labels] if labels else []
        labels = [str(x) for x in labels if x]
        p["promo_types"] = labels
        for lb in labels:
            label_counts[lb] = label_counts.get(lb, 0) + 1
        if label_f:
            low = [str(x).lower() for x in labels]
            if label_f not in low and not any(label_f in x for x in low):
                continue
        by_ep.setdefault(ep_n, []).append(p)

    def _score(p):
        for k in ("series_global_score", "overall_score", "score", "final_score"):
            v = p.get(k)
            if v is None:
                continue
            try:
                return float(v)
            except Exception:
                pass
        return 0.0

    episodes_out = []
    for ep_n in sorted(by_ep.keys()):
        rows = sorted(by_ep[ep_n], key=_score, reverse=True)
        # de-dupe similar
        seen = set()
        uniq = []
        for p in rows:
            key = (
                str(p.get("start_tc") or p.get("start_sec") or ""),
                str(p.get("end_tc") or p.get("end_sec") or ""),
                str(p.get("hook") or p.get("logline") or "")[:80],
            )
            if key in seen:
                continue
            seen.add(key)
            uniq.append(p)
        take = uniq[:top_n]
        for i, p in enumerate(take):
            p["rank_in_episode"] = i + 1
        episodes_out.append({
            "episode": ep_n,
            "count": len(take),
            "total_available": len(uniq),
            "promos": take,
        })

    return {
        "episodes": episodes_out,
        "label_counts": dict(sorted(label_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "top_n": top_n,
        "total_episodes": len(_unique_eps(pool)),
        "episodes_shown": len(episodes_out),
        "pool_size": len(pool),
        "filter": {"label": label_f, "episode": ep_f},
    }

def all_labels() -> List[str]:
    with _LOCK:
        pool = list(_STATE.get("episode_pool") or [])
        pack = list((_STATE.get("doc") or {}).get("campaign_pack") or [])
    c = Counter()
    for p in pool + pack:
        for t in p.get("promo_types") or []:
            c[t] += 1
    return [k for k, _ in c.most_common()]


def build_excel_bytes(
    which: str = "campaign",
    top_n: int = 3,
    label: Optional[str] = None,
) -> BytesIO:
    """Problem-statement Excel only:
    episode, start/end of every segment in order, hook, cliffhanger, why it works.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    if which == "episode":
        data = get_episode_promos(top_n=top_n, label=label)
        rows_src: List[Dict[str, Any]] = []
        for block in data["episodes"]:
            for p in block["promos"]:
                rows_src.append(p)
        title = f"Episode top {top_n}" + (f" / {label}" if label else "")
    else:
        rows_src = get_campaign_pack()
        title = "Campaign priority (post first)"

    max_seg = 1
    for p in rows_src:
        # skip full_window master if we also have hook/rise/cliff parts
        segs = [
            s
            for s in (p.get("segments") or [])
            if str(s.get("role") or "").lower() != "full_window"
        ] or (p.get("segments") or [])
        max_seg = max(max_seg, len(segs))

    wb = Workbook()
    ws = wb.active
    ws.title = "Promos"

    header_fill = PatternFill("solid", fgColor="7C3AED")
    header_font = Font(color="FFFFFF", bold=True, name="Figtree", size=11)
    thin = Border(
        left=Side(style="thin", color="E5E7EB"),
        right=Side(style="thin", color="E5E7EB"),
        top=Side(style="thin", color="E5E7EB"),
        bottom=Side(style="thin", color="E5E7EB"),
    )

    # Strict PS columns
    headers = ["Episode"]
    for i in range(1, max_seg + 1):
        headers += [f"Segment {i} Start", f"Segment {i} End"]
    headers += ["Hook", "Cliffhanger", "Why it works"]

    ws.append(headers)
    for col, _ in enumerate(headers, 1):
        cell = ws.cell(1, col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.border = thin

    for p in rows_src:
        segs = [
            s
            for s in (p.get("segments") or [])
            if str(s.get("role") or "").lower() != "full_window"
        ] or (p.get("segments") or [])
        row: List[Any] = [p.get("episode")]
        for i in range(max_seg):
            if i < len(segs):
                s = segs[i]
                row += [
                    s.get("start_tc") or _sec_to_tc(s.get("start_sec") or 0),
                    s.get("end_tc") or _sec_to_tc(s.get("end_sec") or 0),
                ]
            else:
                row += ["", ""]
        row += [
            p.get("hook") or "",
            p.get("cliffhanger") or "",
            p.get("why_it_works") or "",
        ]
        ws.append(row)
        for col in range(1, len(headers) + 1):
            c = ws.cell(ws.max_row, col)
            c.border = thin
            c.alignment = Alignment(wrap_text=True, vertical="top")

    for col in range(1, len(headers) + 1):
        letter = get_column_letter(col)
        h = headers[col - 1]
        if h in ("Hook", "Cliffhanger", "Why it works"):
            ws.column_dimensions[letter].width = 44
        elif "Segment" in h:
            ws.column_dimensions[letter].width = 14
        else:
            ws.column_dimensions[letter].width = 12

    ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = "A2"

    meta = wb.create_sheet("About")
    meta["A1"] = "KuKu Promo Finder - problem-statement export"
    meta["A1"].font = Font(bold=True, size=14, color="7C3AED")
    meta["A3"] = "Required fields (assignment)"
    meta["B3"] = (
        "For each promo: episode; start and end timestamps of every segment, in order; "
        "hook; cliffhanger; one line on why it works."
    )
    meta["A4"] = "Sheet"
    meta["B4"] = title
    meta["A5"] = "Mode"
    meta["B5"] = _STATE.get("mode")
    meta["A6"] = "Generated (UTC)"
    meta["B6"] = datetime.utcnow().isoformat() + "Z"
    meta.column_dimensions["A"].width = 28
    meta.column_dimensions["B"].width = 100

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def scan_folder(folder: str, parse: bool = False) -> Dict[str, Any]:
    """Live folder inspect (+ optional parse into data/processed)."""
    src = Path(folder)
    if not src.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")

    # Accept episode-*.txt or any .txt
    files = sorted(src.glob("episode-*.txt"))
    if not files:
        files = sorted(src.glob("*.txt"))
    if not files:
        raise ValueError("No .txt scripts found in folder")

    episodes_meta: List[Dict[str, Any]] = []
    for f in files:
        # episode number from filename when possible
        num = None
        name = f.name
        for part in name.replace("_", "-").split("-"):
            if part.isdigit():
                num = int(part)
                break
        episodes_meta.append(
            {
                "file": name,
                "path": str(f),
                "number": num,
                "size_kb": round(f.stat().st_size / 1024, 1),
            }
        )

    result: Dict[str, Any] = {
        "source": str(src.resolve()),
        "script_count": len(files),
        "episode_count": len(episodes_meta),
        "episodes": episodes_meta,
        "parsed": None,
        "dest": None,
        "message": f"Found {len(files)} script(s) in folder",
    }

    if not parse:
        return result

    # Copy into working raw dir + parse with project parser
    info = ensure_scripts_linked(str(src))
    result["dest"] = info["dest"]

    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.parser import parse_all

    # Wipe prior processed episodes so this folder doesn't mix with old series
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    for stale in DATA_PROCESSED.glob("ep_*.json"):
        try:
            stale.unlink()
        except OSError:
            pass

    # parse_all writes processed JSON; returns (episodes, ctx)
    try:
        parsed_out = parse_all(raw_dir=str(DATA_RAW), out_dir=str(DATA_PROCESSED))
    except TypeError:
        parsed_out = parse_all()
    series_ctx = None
    if isinstance(parsed_out, tuple) and len(parsed_out) >= 2:
        series_ctx = parsed_out[1]
    else:
        series_ctx = parsed_out

    # Enrich episode meta from processed JSON (only freshly parsed)
    enriched = []
    for ep_path in sorted(DATA_PROCESSED.glob("ep_*.json")):
        try:
            data = _read_json(ep_path)
            ep_id = data.get("id") or ep_path.stem
            num = data.get("episode_number") or data.get("number")
            if num is None:
                digits = "".join(ch for ch in str(ep_id) if ch.isdigit())
                num = int(digits) if digits else None
            scenes = data.get("scenes") or []
            beats = 0
            for sc in scenes:
                beats += len(sc.get("beats") or [])
            enriched.append(
                {
                    "file": ep_path.name,
                    "episode": num,
                    "number": num,
                    "scenes": len(scenes),
                    "beats": beats,
                    "logline": (data.get("logline") or "")[:120],
                }
            )
        except Exception:
            continue

    result["episodes"] = enriched or episodes_meta
    result["parsed"] = len(enriched) if enriched else len(files)
    result["episode_count"] = len(result["episodes"])
    result["message"] = (
        f"Extracted {result['parsed']} episode(s); scenes/beats written to data/processed"
    )
    result["series_context"] = series_ctx is not None
    return result


def ensure_scripts_linked(folder: str) -> Dict[str, Any]:
    """Point data/raw_episodes (or parser input) at the chosen script folder."""
    src = Path(folder)
    if not src.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")
    txts = list(src.glob("*.txt"))
    if not txts:
        raise ValueError("No .txt scripts in folder")

    # Prefer copying into data/raw_episodes for pipeline expectations
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    # clear old txts carefully
    for old in DATA_RAW.glob("*.txt"):
        try:
            old.unlink()
        except OSError:
            pass
    copied = 0
    for t in txts:
        shutil.copy2(t, DATA_RAW / t.name)
        copied += 1
    return {"copied": copied, "dest": str(DATA_RAW), "source": str(src)}


def start_generate_job(
    mode: str = "hybrid",
    folder: Optional[str] = None,
    top_k: int = 5,
    top_n: int = 25,
    use_marketer: bool = True,
    episode_start: int = 1,
    episode_end: int = 50,
) -> str:
    job_id = uuid.uuid4().hex[:10]
    JOBS[job_id] = {
        "id": job_id,
        "status": "queued",
        "mode": mode,
        "progress": 0,
        "message": "Queued",
        "started_at": time.time(),
        "finished_at": None,
        "error": None,
        "result_summary": None,
    }

    def _run():
        job = JOBS[job_id]
        try:
            job["status"] = "running"
            job["message"] = "Preparing scripts..."
            job["progress"] = 5
            nonlocal episode_start, episode_end
            try:
                max_eps = int(os.getenv("DEMO_MAX_EPISODES", "0") or "0")
            except ValueError:
                max_eps = 0
            if os.getenv("DEMO_PUBLIC", "").strip().lower() in ("1", "true", "yes"):
                fl = (folder or "").lower()
                if "married" in fl or "broken soldier" in fl:
                    raise ValueError("Private assignment scripts are not available on the public demo.")
                if max_eps > 0 and (int(episode_end) - int(episode_start) + 1) > max_eps:
                    episode_end = int(episode_start) + max_eps - 1
                    job["message"] = f"Demo cap: running eps {episode_start}-{episode_end} only"
            if folder:
                ensure_scripts_linked(folder)

            # Import inside thread so UI boots even if pipeline deps are heavy
            import sys

            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))

            from src.orchestrator import run_targeted_pipeline
            from src.final_deliverable import write_deliverable

            job["message"] = f"Running {mode} pipeline on eps {episode_start}-{episode_end}..."
            job["progress"] = 15

            # scoring_mode vs mini_arc_mode mapping
            if mode == "rule":
                mini, scoring = "rule", "rule"
            elif mode == "llm":
                mini, scoring = "llm", "llm"
            else:
                mini, scoring = "rule", "hybrid"

            report = run_targeted_pipeline(
                episode_numbers=list(range(int(episode_start), int(episode_end) + 1)),
                top_k=int(top_k),
                mini_arc_mode=mini,
                scoring_mode=scoring,
            )
            job["progress"] = 70
            job["message"] = "Writing campaign deliverable + Marketer pack..."

            OUTPUT_COMPARE.mkdir(parents=True, exist_ok=True)
            harvest_path = OUTPUT_COMPARE / f"promos_{mode}_top{top_k}.json"
            with open(harvest_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            result = write_deliverable(
                str(harvest_path),
                out_dir=str(OUTPUT_FINAL),
                mode_name=mode,
                episode_numbers=list(range(int(episode_start), int(episode_end) + 1)),
                top_n=top_n,
                max_per_episode=2,
                marketer_trim=bool(use_marketer),
                marketer_min_keep=12,
                marketer_max_keep=20,
                marketer_use_llm=False,
            )
            job["progress"] = 90
            job["message"] = "Refreshing UI state..."
            load_mode(mode, force_enrich_pool=True)
            doc = result.get("doc") or {}
            meta = doc.get("campaign_meta") or {}
            job["result_summary"] = {
                "campaign_n": len(doc.get("campaign_pack") or []),
                "episodes": doc.get("total_episodes_with_promo"),
                "json": result.get("json"),
                "csv": result.get("csv"),
                "marketer": meta.get("marketer"),
            }
            job["progress"] = 100
            job["status"] = "done"
            job["message"] = "Complete"
            job["finished_at"] = time.time()
        except Exception as e:
            job["status"] = "error"
            job["error"] = str(e)
            job["message"] = f"Failed: {e}"
            job["finished_at"] = time.time()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return job_id


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    job = JOBS.get(job_id)
    if not job:
        return None
    # return a shallow copy so callers never mutate internal state oddly
    return dict(job)


# ── Multi-project workspace ──────────────────────────────────────────

PROJECTS_ROOT = ROOT / "data" / "projects"
PROJECTS_INDEX = PROJECTS_ROOT / "index.json"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _read_projects_index() -> Dict[str, Any]:
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    if PROJECTS_INDEX.is_file():
        try:
            data = _read_json(PROJECTS_INDEX)
            if isinstance(data, dict):
                data.setdefault("projects", [])
                data.setdefault("active_id", None)
                return data
        except Exception:
            pass
    return {"projects": [], "active_id": None}


def _write_projects_index(data: Dict[str, Any]) -> None:
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    with open(PROJECTS_INDEX, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _project_dir(project_id: str) -> Path:
    return PROJECTS_ROOT / project_id


def _project_scripts(project_id: str) -> Path:
    return _project_dir(project_id) / "scripts"


def _project_output(project_id: str) -> Path:
    return _project_dir(project_id) / "output"


def list_projects() -> List[Dict[str, Any]]:
    idx = _read_projects_index()
    out = []
    for p in idx.get("projects") or []:
        if not isinstance(p, dict):
            continue
        pid = p.get("id")
        if not pid:
            continue
        scripts = _project_scripts(pid)
        n_scripts = len(list(scripts.glob("*.txt"))) if scripts.is_dir() else 0
        item = dict(p)
        item["script_count"] = n_scripts
        item["has_results"] = bool(
            p.get("last_result")
            or (_project_output(pid) / "FINAL_PROMOS.json").is_file()
            or any((_project_output(pid)).glob("FINAL_PROMOS_*.json"))
            if _project_output(pid).is_dir()
            else False
        )
        item["active"] = pid == idx.get("active_id")
        out.append(item)
    out.sort(key=lambda x: x.get("updated_at") or x.get("created_at") or "", reverse=True)
    return out


def get_active_project_id() -> Optional[str]:
    return _read_projects_index().get("active_id")


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    for p in list_projects():
        if p.get("id") == project_id:
            return p
    return None


def create_project(name: str, description: str = "") -> Dict[str, Any]:
    name = (name or "").strip() or "Untitled project"
    pid = uuid.uuid4().hex[:10]
    scripts = _project_scripts(pid)
    out = _project_output(pid)
    scripts.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    meta = {
        "id": pid,
        "name": name,
        "description": (description or "").strip(),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "status": "empty",  # empty | scripts | running | ready | error
        "mode": None,
        "last_result": None,
        "error": None,
    }
    with open(_project_dir(pid) / "project.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    idx = _read_projects_index()
    idx.setdefault("projects", []).append(meta)
    idx["active_id"] = pid
    _write_projects_index(idx)
    return meta


def _update_project_meta(project_id: str, **fields: Any) -> Dict[str, Any]:
    idx = _read_projects_index()
    found = None
    for p in idx.get("projects") or []:
        if p.get("id") == project_id:
            p.update(fields)
            p["updated_at"] = _now_iso()
            found = p
            break
    if not found:
        raise FileNotFoundError(f"Project not found: {project_id}")
    _write_projects_index(idx)
    meta_path = _project_dir(project_id) / "project.json"
    try:
        cur = _read_json(meta_path) if meta_path.is_file() else {}
        if not isinstance(cur, dict):
            cur = {}
        cur.update(found)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(cur, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return found


def set_active_project(project_id: Optional[str]) -> Dict[str, Any]:
    idx = _read_projects_index()
    if project_id:
        if not any(p.get("id") == project_id for p in (idx.get("projects") or [])):
            raise FileNotFoundError(f"Project not found: {project_id}")
        idx["active_id"] = project_id
        _write_projects_index(idx)
        # Load project results into UI state if present
        loaded = load_project_results(project_id)
        return {"active_id": project_id, "project": get_project(project_id), "loaded": loaded}
    idx["active_id"] = None
    _write_projects_index(idx)
    with _LOCK:
        _STATE["doc"] = {}
        _STATE["episode_pool"] = []
        _STATE["mode"] = None
        _STATE["source_path"] = None
    return {"active_id": None, "project": None, "loaded": False}


def delete_project(project_id: str) -> Dict[str, Any]:
    proj = get_project(project_id)
    lock_seed = os.getenv("DEMO_LOCK_SEED", "1").strip().lower() not in ("0", "false", "no")
    if lock_seed and proj and (
        proj.get("is_seed_demo") or project_id == os.getenv("DEMO_SEED_ID", "e3226269c4")
    ):
        raise PermissionError(
            "The public seed demo project is locked. Create a new project to try your own scripts."
        )
    idx = _read_projects_index()
    idx["projects"] = [p for p in (idx.get("projects") or []) if p.get("id") != project_id]
    if idx.get("active_id") == project_id:
        idx["active_id"] = None
        with _LOCK:
            _STATE["doc"] = {}
            _STATE["episode_pool"] = []
            _STATE["mode"] = None
    _write_projects_index(idx)
    pdir = _project_dir(project_id)
    if pdir.is_dir():
        shutil.rmtree(pdir, ignore_errors=True)
    return {"ok": True, "deleted": project_id}


def save_project_scripts(
    project_id: str,
    files: List[Any],
) -> Dict[str, Any]:
    """Save uploaded .txt scripts into the project folder and parse them."""
    # Public host: cap uploads so free tier / Groq quota stay usable
    n_txt = 0
    for uf in files or []:
        name = getattr(uf, "filename", None) or getattr(uf, "name", None) or ""
        if str(name).lower().endswith(".txt"):
            n_txt += 1
    try:
        max_eps = int(os.getenv("DEMO_MAX_EPISODES", "0") or "0")
    except ValueError:
        max_eps = 0
    if max_eps > 0 and n_txt > max_eps:
        raise ValueError(
            f"Public demo limit: at most {max_eps} episode .txt files "
            f"(you selected {n_txt}). Split the pack or run locally for full seasons."
        )
    if not get_project(project_id):
        raise FileNotFoundError(f"Project not found: {project_id}")

    # Enforce DEMO_MAX_EPISODES at upload time (before wiping existing scripts).
    txt_count = 0
    for uf in files or []:
        name = Path(getattr(uf, "filename", "") or "").name
        if name.lower().endswith(".txt"):
            txt_count += 1
    try:
        max_eps = int(os.getenv("DEMO_MAX_EPISODES", "0") or "0")
    except ValueError:
        max_eps = 0
    if max_eps > 0 and txt_count > max_eps:
        raise ValueError(
            f"Public demo limit: at most {max_eps} episode .txt files per upload "
            f"(you selected {txt_count}). Remove extras or run locally without DEMO_MAX_EPISODES."
        )

    scripts = _project_scripts(project_id)
    scripts.mkdir(parents=True, exist_ok=True)
    # clear previous scripts
    for old in scripts.glob("*.txt"):
        try:
            old.unlink()
        except OSError:
            pass
    saved = []
    for uf in files:
        name = Path(getattr(uf, "filename", "") or "").name
        if not name.lower().endswith(".txt"):
            continue
        dest = scripts / name
        # UploadFile or raw bytes
        if hasattr(uf, "file"):
            with open(dest, "wb") as out:
                shutil.copyfileobj(uf.file, out)
        elif hasattr(uf, "read"):
            data = uf.read()
            with open(dest, "wb") as out:
                out.write(data if isinstance(data, (bytes, bytearray)) else bytes(data))
        else:
            continue
        saved.append(name)
    if not saved:
        raise ValueError("No .txt script files received. Upload episode .txt files.")
    _update_project_meta(
        project_id,
        status="scripts",
        script_count=len(saved),
        last_result=None,
        error=None,
    )
    # Parse immediately so user sees episode list
    parse_info = scan_folder(str(scripts), parse=True)
    return {
        "project_id": project_id,
        "saved": saved,
        "count": len(saved),
        "folder": str(scripts),
        "parse": parse_info,
    }


def load_project_results(project_id: str) -> bool:
    """Load FINAL deliverable for a project into UI state. Returns True if loaded."""
    out = _project_output(project_id)
    candidates = [
        out / "FINAL_PROMOS.json",
        out / "FINAL_PROMOS_hybrid.json",
        out / "FINAL_PROMOS_rule.json",
        out / "FINAL_PROMOS_llm.json",
    ]
    if out.is_dir():
        candidates.extend(sorted(out.glob("FINAL_PROMOS*.json"), reverse=True))
    path = next((p for p in candidates if p.is_file()), None)
    if not path:
        with _LOCK:
            # Only clear if this project is the one loaded (don't wipe another project's data)
            if _STATE.get("project_id") in (None, project_id):
                _STATE["doc"] = {}
                _STATE["episode_pool"] = []
                _STATE["campaign_pack"] = []
                _STATE["per_episode_best"] = []
                _STATE["mode"] = None
                _STATE["source_path"] = None
            _STATE["project_id"] = project_id
        return False
    try:
        doc = _read_json(path)
    except Exception as e:
        print(f"[web] failed reading {path}: {e}")
        return False
    if not isinstance(doc, dict):
        return False
    mode = doc.get("mode") or ((doc.get("meta") or {}).get("scoring_mode")) or "hybrid"
    pack = doc.get("campaign_pack") or []
    peb = doc.get("per_episode_best") or []
    # Normalize ranks for UI (campaign pack only — do not break pack order)
    for i, p in enumerate(pack):
        if not isinstance(p, dict):
            continue
        p.setdefault("campaign_rank", i + 1)
        p.setdefault("post_rank", i + 1)
    try:
        episode_pool = _build_episode_pool_from_project(project_id, doc)
    except Exception as e:
        print(f"[web] build episode pool failed: {e}")
        episode_pool = []
        for src in (pack, peb):
            for p in src or []:
                if isinstance(p, dict):
                    try:
                        episode_pool.append(_enrich_promo(p))
                    except Exception:
                        try:
                            episode_pool.append(_normalize_promo(p))
                        except Exception:
                            episode_pool.append(dict(p))
    # Second pass: fill any remaining empty hooks (processed ep JSON is cached; ~ms each)
    try:
        fixed = 0
        for i, p in enumerate(list(episode_pool)):
            if not isinstance(p, dict):
                continue
            need = (not str(p.get("hook") or "").strip()) or _is_placeholder_why(p.get("why_it_works"))
            if not need:
                continue
            try:
                episode_pool[i] = _enrich_promo(p)
                fixed += 1
            except Exception:
                pass
        if fixed:
            print(f"[web] post-enriched {fixed} episode-pool promos")
    except Exception as e:
        print(f"[web] post-enrich failed: {e}")
    cont_path = out / "series_continuity_map.json"
    cont_hint = {"path": str(cont_path), "project_id": project_id} if cont_path.exists() else None
    with _LOCK:
        _STATE["doc"] = doc
        _STATE["mode"] = mode
        _STATE["source_path"] = str(path)
        _STATE["loaded_at"] = time.time()
        _STATE["project_id"] = project_id
        _STATE["campaign_pack"] = [dict(p) for p in pack if isinstance(p, dict)]
        _STATE["per_episode_best"] = [dict(p) for p in peb if isinstance(p, dict)]
        _STATE["episode_pool"] = list(episode_pool)
        if cont_hint:
            existing = _STATE.get("continuity_map")
            if not existing or not (existing.get("arcs") or existing.get("path")):
                _STATE["continuity_map"] = cont_hint
            elif isinstance(existing, dict) and not existing.get("path"):
                merged = dict(existing)
                merged["path"] = str(cont_path)
                _STATE["continuity_map"] = merged
    print(
        f"[web] loaded project={project_id} path={path.name} pack={len(pack)} "
        f"peb={len(peb) if isinstance(peb, list) else 0} pool={len(episode_pool)} mode={mode}"
    )
    return True


def start_project_pipeline(
    project_id: str,
    mode: str = "hybrid",
    top_k: int = 5,
    top_n: int = 25,
    use_marketer: bool = True,
) -> str:
    """Run full src pipeline for a project’s uploaded scripts."""
    proj = get_project(project_id)
    if not proj:
        raise FileNotFoundError(f"Project not found: {project_id}")
    scripts = _project_scripts(project_id)
    txts = list(scripts.glob("*.txt")) if scripts.is_dir() else []
    if not txts:
        raise ValueError(
            "Upload episode .txt scripts before running the pipeline. "
            "The public demo ships outputs only (scripts stay private)."
        )
    try:
        max_eps = int(os.getenv("DEMO_MAX_EPISODES", "0") or "0")
    except ValueError:
        max_eps = 0
    if max_eps > 0 and len(txts) > max_eps:
        raise ValueError(
            f"Public demo limit: at most {max_eps} episode .txt files per run "
            f"(you uploaded {len(txts)}). Split the pack or run locally for full seasons."
        )

    # Detect episode range from filenames / parse
    parse_info = scan_folder(str(scripts), parse=False)
    episodes = []
    for ep in parse_info.get("episodes") or []:
        try:
            n = ep.get("episode")
            if n is None:
                n = ep.get("number")
            if n is not None:
                episodes.append(int(n))
        except Exception:
            pass
    if not episodes:
        # fallback 1..n
        episodes = list(range(1, len(txts) + 1))
    episodes = sorted(set(e for e in episodes if e and e > 0))
    if not episodes:
        episodes = list(range(1, len(txts) + 1))
    episode_start, episode_end = min(episodes), max(episodes)

    job_id = uuid.uuid4().hex[:10]
    JOBS[job_id] = {
        "id": job_id,
        "status": "queued",
        "mode": mode,
        "project_id": project_id,
        "progress": 0,
        "message": "Queued",
        "started_at": time.time(),
        "finished_at": None,
        "error": None,
        "result_summary": None,
    }
    # Cancel any other running jobs so the UI isn't stuck on a dead poll
    for other in list(JOBS.values()):
        if other.get("status") in ("queued", "running") and other.get("id") != job_id:
            other["status"] = "error"
            other["error"] = "Superseded by a newer run"
            other["message"] = "Cancelled — newer pipeline started"
            other["finished_at"] = time.time()

    _update_project_meta(project_id, status="running", mode=mode, error=None)
    # Mark active without reloading stale results mid-run
    idx = _read_projects_index()
    idx["active_id"] = project_id
    _write_projects_index(idx)

    def _run():
        job = JOBS[job_id]
        try:
            job["status"] = "running"
            job["message"] = "Linking scripts into pipeline…"
            job["progress"] = 5
            ensure_scripts_linked(str(scripts))

            # Parse + continuity map via live parse (writes processed)
            job["message"] = "Parsing scripts (beats / scenes)…"
            job["progress"] = 12
            scan_folder(str(scripts), parse=True)

            import sys

            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))

            from src.orchestrator import run_targeted_pipeline
            from src.final_deliverable import write_deliverable

            job["message"] = (
                f"Running {mode} pipeline on episodes {episode_start}–{episode_end} "
                f"(this can take a few minutes)…"
            )
            job["progress"] = 20

            if mode == "rule":
                mini, scoring = "rule", "rule"
            elif mode == "llm":
                mini, scoring = "llm", "llm"
            else:
                # hybrid: rule mini-arc + hybrid scoring (falls back to rule if no key)
                mini, scoring = "rule", "hybrid"

            # Heartbeat so the UI doesn't look frozen during long LLM waves
            stop_hb = threading.Event()

            def _heartbeat():
                n = 0
                while not stop_hb.wait(4.0):
                    n += 1
                    if job.get("status") != "running":
                        break
                    base = 20 + min(40, n)  # 20 → 60
                    job["progress"] = max(int(job.get("progress") or 20), base)
                    job["message"] = (
                        f"Pipeline running ({mode}) · episodes {episode_start}–{episode_end} · "
                        f"still working… {n * 4}s"
                    )

            hb = threading.Thread(target=_heartbeat, daemon=True)
            hb.start()
            try:
                report = run_targeted_pipeline(
                    episode_numbers=list(range(int(episode_start), int(episode_end) + 1)),
                    top_k=int(top_k),
                    mini_arc_mode=mini,
                    scoring_mode=scoring,
                )
            finally:
                stop_hb.set()

            job["progress"] = 72
            job["message"] = "Writing campaign pack + Marketer QA…"

            proj_out = _project_output(project_id)
            proj_out.mkdir(parents=True, exist_ok=True)
            OUTPUT_COMPARE.mkdir(parents=True, exist_ok=True)
            harvest_path = proj_out / f"promos_{mode}_top{top_k}.json"
            # report may be dict already
            if not isinstance(report, dict):
                report = {"episodes": report}
            with open(harvest_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            try:
                shutil.copy2(harvest_path, OUTPUT_COMPARE / harvest_path.name)
            except Exception:
                pass

            result = write_deliverable(
                str(harvest_path),
                out_dir=str(proj_out),
                mode_name=mode,
                episode_numbers=list(range(int(episode_start), int(episode_end) + 1)),
                top_n=top_n,
                max_per_episode=2,
                marketer_trim=bool(use_marketer),
                marketer_min_keep=12,
                marketer_max_keep=20,
                marketer_use_llm=False,
            )
            # Normalize final name — write_deliverable returns "json" path
            final_json = result.get("json") or result.get("json_path")
            if final_json:
                try:
                    src_final = Path(final_json)
                    if src_final.is_file():
                        shutil.copy2(src_final, proj_out / "FINAL_PROMOS.json")
                        shutil.copy2(src_final, proj_out / f"FINAL_PROMOS_{mode}.json")
                except Exception:
                    pass
            # Prefer explicit FINAL already in proj_out
            if not (proj_out / "FINAL_PROMOS.json").is_file():
                # copy any FINAL_PROMOS_*.json written by deliverable
                for cand in sorted(proj_out.glob("FINAL_PROMOS*.json")):
                    try:
                        shutil.copy2(cand, proj_out / "FINAL_PROMOS.json")
                        break
                    except Exception:
                        pass

            job["progress"] = 90
            job["message"] = "Loading results into workspace…"
            ok_load = load_project_results(project_id)
            # Mirror into global final for Excel export compatibility
            try:
                src_final2 = proj_out / "FINAL_PROMOS.json"
                if src_final2.is_file():
                    OUTPUT_FINAL.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_final2, OUTPUT_FINAL / f"FINAL_PROMOS_{mode}.json")
            except Exception:
                pass

            doc = result.get("doc") or (_STATE.get("doc") or {})
            pack = doc.get("campaign_pack") or []
            meta = doc.get("campaign_meta") or {}
            summary = {
                "campaign_n": len(pack),
                "episodes": doc.get("total_episodes_with_promo"),
                "json": str(proj_out / "FINAL_PROMOS.json"),
                "csv": result.get("csv"),
                "marketer": meta.get("marketer"),
                "project_id": project_id,
                "episode_start": episode_start,
                "episode_end": episode_end,
                "loaded": ok_load,
            }
            job["result_summary"] = summary
            job["progress"] = 100
            job["status"] = "done"
            job["message"] = f"Complete — {len(pack)} promos in priority list"
            job["finished_at"] = time.time()
            _update_project_meta(
                project_id,
                status="ready",
                mode=mode,
                last_result=summary,
                error=None,
            )
        except Exception as e:
            job["status"] = "error"
            job["error"] = str(e)
            job["message"] = f"Failed: {e}"
            job["finished_at"] = time.time()
            try:
                _update_project_meta(project_id, status="error", error=str(e))
            except Exception:
                pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return job_id


def bootstrap() -> None:
    """Boot projects index. Prefer seed demo / project with deliverable results."""
    try:
        PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
        seed_id = os.getenv("DEMO_SEED_ID", "e3226269c4")
        seed_out = PROJECTS_ROOT / seed_id / "output"
        if seed_out.is_dir() and any(seed_out.glob("FINAL_PROMOS*.json")):
            (PROJECTS_ROOT / seed_id / "scripts").mkdir(parents=True, exist_ok=True)

        idx = _read_projects_index()
        projects = list(idx.get("projects") or [])
        active = idx.get("active_id")

        def _has_results(pid: str) -> bool:
            out = _project_output(str(pid))
            if not out.is_dir():
                return False
            return bool(list(out.glob("FINAL_PROMOS*.json")))

        # Prefer seed demo, then any project with results
        if not active or not _has_results(str(active)):
            preferred: List[str] = []
            if seed_id and _has_results(seed_id):
                preferred.append(seed_id)
            for p in projects:
                pid = str(p.get("id") or "")
                if pid and pid not in preferred and _has_results(pid):
                    preferred.append(pid)
            if preferred:
                active = preferred[0]
                idx["active_id"] = active
                _write_projects_index(idx)
                print(f"[web] bootstrap active → {active}")

        if active:
            ok = load_project_results(str(active))
            with _LOCK:
                n_pool = len(_STATE.get("episode_pool") or [])
                n_ep = len(
                    {
                        int(x.get("episode") or 0)
                        for x in (_STATE.get("episode_pool") or [])
                        if isinstance(x, dict)
                    }
                )
            print(f"[web] bootstrapped project={active} results={ok} pool={n_pool} eps={n_ep}")
        else:
            print("[web] bootstrapped empty workspace")
    except Exception as e:
        print("[web] bootstrap load failed: %s" % e)

