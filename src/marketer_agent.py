"""Marketer Agent — campaign pack QA / trim.

Job: remove weak tail promos from the campaign pack WITHOUT killing already-strong
ones. Runs after global scoring + diversity pack.

Design:
  1) PROTECT hard: high global score, high local quality, strong hook craft
  2) GATE soft: thin hooks, empty address lines, bad duration, degenerate segments,
     low clarity dumps — only if NOT protected
  3) RELATIVE trim: if pack still oversized, drop lowest unprotected first
  4) Optional LLM second opinion on BORDERLINE only (never on protected keep/cut)

Classification labels (promo_types) never decide keep/cut.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple


# ---- thresholds (tuned to keep top tier, cut "Your Grace." class) ----

# Hard protect — never cut these
PROTECT_GLOBAL = 7.85
PROTECT_OVERALL = 8.0
PROTECT_TOP_K = 10  # first K by campaign_rank / global always protected
PROTECT_CLARITY = 7.5
PROTECT_HOOK_WORDS = 6

# Fail gates (only apply if not protected)
MIN_HOOK_WORDS = 4
MIN_CLIFF_WORDS = 4
MIN_DURATION = 14.0
MAX_DURATION = 62.0
MIN_OVERALL_UNPROTECTED = 6.45
MIN_GLOBAL_UNPROTECTED = 7.15
MIN_CLARITY_UNPROTECTED = 5.2

# Address / filler hooks that are almost never cold-open material alone
THIN_HOOK_PATTERNS = [
    r"^your grace\.?$",
    r"^my lady\.?$",
    r"^my lord\.?$",
    r"^yes\.?$",
    r"^no\.?$",
    r"^what\??$",
    r"^who\??$",
    r"^please\.?$",
    r"^wait\.?$",
    r"^i am\.?$",
    r"^i'm\.?$",
    r"^sir\.?$",
    r"^ma'am\.?$",
    r"^hello\.?$",
    r"^oh\.?$",
    r"^ah\.?$",
    r"^thank you\.?$",
    r"^thanks\.?$",
    r"^miss \w+\.?$",
    r"^mr\.? \w+\.?$",
    r"^lady \w+\.?$",
    r"^lord \w+\.?$",
]

# Content that usually means a real story hook
STRONG_HOOK_SIGNALS = [
    "never", "betray", "dead", "kill", "love", "father", "mother", "forgive",
    "truth", "lie", "blood", "marry", "wedding", "protect", "survive", "dare",
    "swear", "disown", "choose", "chose", "die", "poison", "secret", "hate",
    "mine", "leave", "stay", "together", "wound", "heir", "duke", "hand",
    "trust", "trusted", "humiliate", "cruel", "vows", "wife", "husband",
    "worth", "forgive", "embarra", "burn", "wound", "declared", "servant",
    "remember", "speak", "found", "alive", "steal", "stole", "stolen",
    "wedding", "locket", "worthy", "embarra",
]


def _f(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def _words(text: str) -> List[str]:
    return re.findall(r"[A-Za-z']+", text or "")


def _norm_line(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


_STAGE_DIR = re.compile(
    r"^(medium |close-?up|wide |extreme |tracking |shot |cut to|camera |"
    r"we see|the camera|fade |int\.|ext\.)",
    re.I,
)


def _is_stage_direction(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    if _STAGE_DIR.search(t):
        return True
    tl = t.lower()
    # pure action line without dialogue quotes
    if '"' not in t and not t.startswith("'"):
        if re.match(
            r"^(he|she|they|her|his|juliana|alexander|gerald|clarissa)\s+\w+",
            t,
            re.I,
        ):
            # "Her hand rises..." / "Juliana clutches..." — not cold dialogue
            if not any(s in tl for s in ("never", "betray", "dead", "love", "kill", "forgive", "steal")):
                return True
        if re.search(r"\b(rises|clutches|walks|turns|looks|stares|enters|exits)\b", tl):
            if len(_words(t)) < 16 and not any(
                s in tl for s in ("never", "betray", "dead", "love you", "forgive")
            ):
                return True
    return False


def _clean_hook_line(text: str) -> str:
    t = (text or "").strip().strip('"').strip()
    # drop trailing stage direction glued after dialogue
    t = re.split(
        r'\s+(?:Medium |Close-?up|Wide |Extreme |Tracking |Shot |Cut to|Camera )',
        t,
        maxsplit=1,
        flags=re.I,
    )[0].strip()
    t = t.strip('"').strip()
    return t


def _score_hook_candidate(text: str) -> float:
    """Higher = better cold-open dialogue line."""
    t = _clean_hook_line(text)
    if not t or _is_stage_direction(t) or _is_thin_hook_raw(t):
        return -1.0
    h = t.lower()
    words = _words(t)
    # cap keyword spam so long monologues don't beat punchy lines
    hits = sum(1 for s in STRONG_HOOK_SIGNALS if s in h)
    score = min(6.0, len(words) * 0.25)
    score += min(3.0, 1.2 * hits)
    if "?" in t:
        score += 0.8
    # prefer punchy 4–12 words over monologues
    n = len(words)
    if 4 <= n <= 8:
        score += 3.5
    elif 9 <= n <= 14:
        score += 2.0
    elif 15 <= n <= 22:
        score += 0.2
    elif n > 22:
        score -= 2.0
    # ellipsis fragments like "...still clinging"
    if t.startswith("..."):
        score -= 3.5
    return score


def _first_solid_sentence(text: str, min_words: int = 5) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    candidates = []
    # only well-closed short quotes (avoid unclosed "Look at you... swallowing the rest)
    for q in re.findall(r'"([^"\n]{6,120})"', t):
        candidates.append(_clean_hook_line(q))
    parts = re.split(r"(?<=[.!?])\s+|\n+", t)
    for part in parts:
        part = _clean_hook_line(part)
        if part:
            candidates.append(part)
    best = ""
    best_s = -1.0
    for i, c in enumerate(candidates):
        c = _clean_hook_line(c)
        s = _score_hook_candidate(c)
        # slight preference for earlier lines (cold open)
        s += max(0.0, 0.6 - i * 0.05)
        if s > best_s:
            best_s = s
            best = c
    return best if best_s >= 0 else ""


def _raw_hook(p: Dict[str, Any]) -> str:
    return (p.get("hook") or p.get("trigger_text") or "").strip()


def _hook_text(p: Dict[str, Any]) -> str:
    """Prefer enriched hook; else best solid line from trigger/window."""
    h = (p.get("hook") or "").strip()
    if h and not _is_thin_hook_raw(h):
        return h
    for key in ("trigger_text", "window_text"):
        cand = _first_solid_sentence(p.get(key) or "", min_words=5)
        if cand and not _is_thin_hook_raw(cand):
            return cand
    # fall back to given hook/trigger even if thin (so we can cut it)
    return h or (p.get("trigger_text") or "").strip() or _first_solid_sentence(
        p.get("window_text") or "", min_words=1
    )


def _maybe_upgrade_hook_fields(p: Dict[str, Any]) -> Dict[str, Any]:
    """If stored hook is thin/stagey but window has a real line, write it onto the card."""
    row = dict(p)
    raw = _clean_hook_line(_raw_hook(p))
    best = _clean_hook_line(_hook_text(p))
    raw_bad = _is_thin_hook_raw(raw) or _is_stage_direction(raw) or _score_hook_candidate(raw) < 2.0
    if best and not _is_thin_hook_raw(best) and not _is_stage_direction(best):
        if raw_bad or _score_hook_candidate(best) > _score_hook_candidate(raw) + 0.5:
            row["hook"] = best
            row["marketer_hook_upgraded"] = True
    elif raw:
        row["hook"] = raw  # cleaned
    cliff = _clean_hook_line(_cliff_text(p))
    if cliff and len(_words(cliff)) >= MIN_CLIFF_WORDS:
        cur = (p.get("cliffhanger") or "").strip()
        if _is_thin_hook_raw(cur) or not cur or _is_stage_direction(cur):
            row["cliffhanger"] = cliff
            row["marketer_cliff_upgraded"] = True
    return row


def _cliff_text(p: Dict[str, Any]) -> str:
    c = (p.get("cliffhanger") or "").strip()
    if c and len(_words(c)) >= MIN_CLIFF_WORDS:
        return c
    # last solid sentence of window often is the open loop
    wt = (p.get("window_text") or "").strip()
    if wt:
        parts = re.split(r"(?<=[.!?])\s+|\n+", wt)
        for part in reversed(parts):
            if len(_words(part)) >= MIN_CLIFF_WORDS:
                return part.strip()
    return c or (p.get("hook") or "").strip()


def _is_thin_hook_raw(hook: str) -> bool:
    """Thin check without recursion (used while selecting hook text)."""
    h = _norm_line(hook)
    if not h:
        return True
    words = _words(h)
    if any(s in h for s in STRONG_HOOK_SIGNALS) and len(words) >= 3:
        return False
    if len(words) < MIN_HOOK_WORDS:
        return True
    for pat in THIN_HOOK_PATTERNS:
        if re.match(pat, h, flags=re.I):
            return True
    if len(words) <= 2 and not any(s in h for s in STRONG_HOOK_SIGNALS):
        if len(words) == 1:
            return True
    return False


def _bd(p: Dict[str, Any]) -> Dict[str, Any]:
    return p.get("series_breakdown") or {}


def _global(p: Dict[str, Any]) -> float:
    return _f(p.get("series_global_score", p.get("series_score")), 0.0)


def _is_thin_hook(hook: str) -> bool:
    return _is_thin_hook_raw(hook)


def _has_strong_hook_craft(hook: str) -> bool:
    h = _norm_line(hook)
    words = _words(h)
    if len(words) >= PROTECT_HOOK_WORDS and any(s in h for s in STRONG_HOOK_SIGNALS):
        return True
    if "?" in hook and len(words) >= 5:
        return True
    if len(words) >= 8:
        return True
    return False


def _degenerate_segments(p: Dict[str, Any]) -> bool:
    segs = p.get("segments") or []
    if not segs:
        return False  # missing segs not enough alone to kill
    bad = 0
    for s in segs:
        try:
            a = float(s.get("start_sec") or 0)
            b = float(s.get("end_sec") or 0)
        except (TypeError, ValueError):
            bad += 1
            continue
        if b <= a + 0.05:
            bad += 1
    # kill only if majority degenerate
    return bad >= max(1, len(segs) // 2 + 1)


def is_protected(p: Dict[str, Any], pack_index: int = 999) -> Tuple[bool, str]:
    """Strong promos the marketer must not remove."""
    g = _global(p)
    overall = _f(p.get("overall_score"), 0.0)
    clarity = _f(_bd(p).get("standalone_clarity"), 5.0)
    hook = _hook_text(p)
    cliff = _cliff_text(p)

    if pack_index < PROTECT_TOP_K:
        return True, f"top_{PROTECT_TOP_K}_slot"
    if g >= PROTECT_GLOBAL:
        return True, f"global>={PROTECT_GLOBAL}"
    if overall >= PROTECT_OVERALL and clarity >= 6.5 and not _is_thin_hook(hook):
        return True, f"overall>={PROTECT_OVERALL}+clarity"
    if (
        g >= 7.55
        and _has_strong_hook_craft(hook)
        and len(_words(cliff)) >= MIN_CLIFF_WORDS
        and clarity >= PROTECT_CLARITY
    ):
        return True, "strong_craft+clarity"
    # acquisition + clear + decent global
    role = _bd(p).get("campaign_role") or ""
    if role == "acquisition" and g >= 7.6 and clarity >= 7.0 and not _is_thin_hook(hook):
        return True, "acquisition_keeper"
    return False, ""


def evaluate_promo(
    p: Dict[str, Any],
    pack_index: int = 999,
) -> Dict[str, Any]:
    """Return keep/cut decision with reasons.

    Thin/empty hooks and degenerate segments are HARD cuts — they override
    protect. Protect only saves strong, already-good promos from soft/size cuts.
    """
    hook = _hook_text(p)
    cliff = _cliff_text(p)
    g = _global(p)
    overall = _f(p.get("overall_score"), 0.0)
    dur = _f(p.get("duration_sec"), _f((p.get("timecode") or {}).get("duration_sec"), 0.0))
    clarity = _f(_bd(p).get("standalone_clarity"), 5.0)
    fit = _f(_bd(p).get("continuity_fit"), 5.0)

    protected, protect_reason = is_protected(p, pack_index=pack_index)
    fails: List[str] = []
    soft_flags: List[str] = []

    # Quality gates
    thin = _is_thin_hook(hook)
    if thin:
        fails.append("thin_or_empty_hook")
    if len(_words(cliff)) < MIN_CLIFF_WORDS:
        fails.append("thin_cliffhanger")
    if dur and (dur < MIN_DURATION or dur > MAX_DURATION):
        fails.append(f"duration_out_of_range({dur}s)")
    if overall and overall < MIN_OVERALL_UNPROTECTED:
        fails.append(f"overall_below_{MIN_OVERALL_UNPROTECTED}")
    if g and g < MIN_GLOBAL_UNPROTECTED:
        fails.append(f"global_below_{MIN_GLOBAL_UNPROTECTED}")
    if clarity < MIN_CLARITY_UNPROTECTED:
        fails.append("low_standalone_clarity")
    if _degenerate_segments(p):
        fails.append("degenerate_segments")

    # Soft (need 2+ soft + not protected to cut, or 1 soft with a hard fail)
    if hook and cliff and _norm_line(hook) == _norm_line(cliff) and len(_words(hook)) < 10:
        soft_flags.append("hook_equals_cliff_short")
    if fit < 4.0 and clarity < 6.0:
        soft_flags.append("weak_fit_and_clarity")
    role = _bd(p).get("campaign_role") or ""
    if role == "payoff" and clarity < 6.5 and g < 7.6:
        soft_flags.append("late_payoff_unclear_for_cold")
    # Weak cold open: short question / low craft late in pack scores
    hw = _words(hook)
    if (
        len(hw) <= 5
        and not _has_strong_hook_craft(hook)
        and g < 7.7
        and overall < 7.6
    ):
        soft_flags.append("soft_short_hook_low_score")
    if _is_stage_direction(hook):
        fails.append("stage_direction_hook")

    cut = False
    reason = "pass"

    # If raw display hook is address-only but we found a better line, don't cut —
    # upgrade path handles it. Only cut when effective hook is still thin.
    raw_thin = _is_thin_hook_raw(_raw_hook(p))
    effective = _hook_text(p)
    thin_effective = _is_thin_hook_raw(effective)
    if thin_effective:
        fails = [f for f in fails if f != "thin_or_empty_hook"] + ["thin_or_empty_hook"]
        thin = True
    elif raw_thin and not thin_effective:
        # raw was thin, effective is good → keep and upgrade
        fails = [f for f in fails if f != "thin_or_empty_hook"]
        thin = False
        soft_flags.append("hook_upgraded_from_thin_raw")

    # HARD cuts always win — a high score cannot save truly empty hooks
    if thin:
        cut = True
        reason = "CUT:thin_hook"
        protected = False
        protect_reason = ""
    elif "degenerate_segments" in fails:
        cut = True
        reason = "CUT:bad_segments"
        protected = False
        protect_reason = ""
    elif "stage_direction_hook" in fails and not _has_strong_hook_craft(hook):
        # try upgrade already happened; still stagey → cut unless protected craft
        if protected and g >= 8.0:
            cut = False
            reason = f"PROTECTED:{protect_reason}"
        else:
            cut = True
            reason = "CUT:stage_direction_hook"
            protected = False
            protect_reason = ""
    elif protected:
        cut = False
        reason = f"PROTECTED:{protect_reason}"
    else:
        if len(fails) >= 2:
            cut = True
            reason = "CUT:" + "+".join(fails[:3])
        elif len(fails) == 1 and len(soft_flags) >= 1:
            cut = True
            reason = "CUT:" + fails[0] + "+" + soft_flags[0]
        elif len(soft_flags) >= 2 and g < 7.55:
            cut = True
            reason = "CUT:soft:" + "+".join(soft_flags[:2])
        elif "soft_short_hook_low_score" in soft_flags and g < 7.5:
            cut = True
            reason = "CUT:soft_short_hook"
        else:
            cut = False
            reason = "KEEP:gates_pass" if not fails else f"KEEP:minor:{','.join(fails)}"

    return {
        "episode": p.get("episode"),
        "campaign_rank": p.get("campaign_rank") or p.get("post_rank"),
        "series_global_score": g,
        "overall_score": overall,
        "protected": protected and not cut,
        "protect_reason": protect_reason,
        "cut": cut,
        "decision": "cut" if cut else "keep",
        "reason": reason,
        "fails": fails,
        "soft_flags": soft_flags,
        "hook_preview": hook[:80],
        "cliff_preview": cliff[:80],
        "drop_priority": _drop_priority(p, fails, soft_flags, thin),
    }


def _drop_priority(
    p: Dict[str, Any],
    fails: List[str],
    soft_flags: List[str],
    thin: bool,
) -> float:
    """Higher = drop first when shrinking pack. Good hooks get low priority."""
    g = _global(p)
    # base: inverse score
    pri = 10.0 - g
    if thin:
        pri += 5.0
    pri += 0.8 * len(fails) + 0.4 * len(soft_flags)
    if _has_strong_hook_craft(_hook_text(p)):
        pri -= 1.5  # keep good story hooks when size-trimming
    clarity = _f(_bd(p).get("standalone_clarity"), 5.0)
    if clarity >= 7.5:
        pri -= 0.4
    return pri


def marketer_trim_pack(
    pack: List[Dict[str, Any]],
    min_keep: int = 12,
    max_keep: int = 20,
    target_keep: Optional[int] = None,
) -> Dict[str, Any]:
    """Apply marketer QA to a ranked campaign pack.

    - Never cuts protected promos
    - Cuts weak ones by gates
    - If still > max_keep, drops lowest-global unprotected first
    - If after cuts < min_keep, re-add best cut unprotected only if they failed
      only on soft/global-floor (never re-add thin_hook)
    """
    if not pack:
        return {
            "campaign_pack": [],
            "cut_list": [],
            "kept": 0,
            "cut_count": 0,
            "protected_count": 0,
            "marketer_log": [],
        }

    # Ensure indices by current order
    ordered = list(pack)
    logs: List[Dict[str, Any]] = []
    keep_rows: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    cut_rows: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []

    for i, p in enumerate(ordered):
        ev = evaluate_promo(p, pack_index=i)
        logs.append(ev)
        if ev["cut"]:
            cut_rows.append((p, ev))
        else:
            keep_rows.append((p, ev))

    # Relative size control: too many kept → trim unprotected from the bottom
    if target_keep is None:
        # Prefer natural keep size, clamp later
        target = min(max_keep, max(min_keep, len(keep_rows)))
    else:
        target = max(min_keep, min(max_keep, int(target_keep)))

    # Sort keep by global desc for any refill; preserve original relative order for output
    def gkey(pair):
        return _global(pair[0])

    if len(keep_rows) > max_keep:
        # Only size-trim WEAK-ish rows. Never drop strong craft just to hit a ceiling.
        prot = [(p, e) for p, e in keep_rows if e.get("protected")]
        unprot = [(p, e) for p, e in keep_rows if not e.get("protected")]

        def _size_drop_ok(pe) -> bool:
            p, e = pe
            hook = _hook_text(p)
            g = _global(p)
            # Never size-drop a clearly good story hook just to hit N
            if _has_strong_hook_craft(hook) and g >= 7.5:
                return False
            if g >= 8.0 and not e.get("fails"):
                return False
            if e.get("fails"):
                return True
            # soft flags alone: only if global is soft
            if e.get("soft_flags") and g < 7.7:
                return True
            if _f(e.get("drop_priority"), 0) >= 2.5 and g < 7.65:
                return True
            # lower third soft global without punchy craft
            if g < 7.55 and not _has_strong_hook_craft(hook):
                return True
            if g < 7.35:
                return True
            return False

        droppable = [pe for pe in unprot if _size_drop_ok(pe)]
        keep_unprot = [pe for pe in unprot if not _size_drop_ok(pe)]
        droppable.sort(
            key=lambda pe: _f(pe[1].get("drop_priority"), 10.0 - _global(pe[0])),
            reverse=True,
        )
        need_drop = len(keep_rows) - max_keep
        dropped = []
        while need_drop > 0 and droppable:
            p, e = droppable.pop(0)
            e = dict(e)
            e["cut"] = True
            e["decision"] = "cut"
            e["reason"] = "CUT:relative_pack_size"
            dropped.append((p, e))
            need_drop -= 1
        # If still over max and only strong left, allow mild overflow (prefer quality)
        keep_rows = prot + keep_unprot + droppable
        keep_rows.sort(key=lambda pe: int(pe[0].get("campaign_rank") or pe[0].get("post_rank") or 999))
        cut_rows.extend(dropped)
        for d in dropped:
            for L in logs:
                if L.get("episode") == d[1].get("episode") and L.get("hook_preview") == d[1].get(
                    "hook_preview"
                ):
                    L.update(d[1])

    # If too few kept, try refill from cuts that weren't thin-hook
    if len(keep_rows) < min_keep and cut_rows:
        cut_rows_sorted = sorted(cut_rows, key=gkey, reverse=True)
        still_cut = []
        for p, e in cut_rows_sorted:
            if len(keep_rows) >= min_keep:
                still_cut.append((p, e))
                continue
            fails = e.get("fails") or []
            if "thin_or_empty_hook" in fails or "degenerate_segments" in fails:
                still_cut.append((p, e))
                continue
            # soft re-admit
            e = dict(e)
            e["cut"] = False
            e["decision"] = "keep"
            e["reason"] = "KEEP:refilled_to_min"
            e["protected"] = False
            keep_rows.append((p, e))
            for L in logs:
                if L.get("hook_preview") == e.get("hook_preview") and L.get("episode") == e.get(
                    "episode"
                ):
                    L.update(e)
        cut_rows = [x for x in cut_rows if x[0] not in {k[0] for k in keep_rows}]
        # rebuild cut_rows properly
        keep_ids = {id(k[0]) for k in keep_rows}
        cut_rows = [(p, e) for p, e in cut_rows_sorted if id(p) not in keep_ids]
        keep_rows.sort(key=lambda pe: int(pe[0].get("campaign_rank") or pe[0].get("post_rank") or 999))

    # Final optional target shrink (if target_keep set tighter)
    if target_keep is not None and len(keep_rows) > target:
        prot = [(p, e) for p, e in keep_rows if e.get("protected")]
        unprot = [(p, e) for p, e in keep_rows if not e.get("protected")]
        unprot.sort(key=gkey)
        while len(prot) + len(unprot) > target and unprot:
            p, e = unprot.pop(0)
            e = dict(e)
            e["cut"] = True
            e["decision"] = "cut"
            e["reason"] = "CUT:target_keep"
            cut_rows.append((p, e))
        keep_rows = prot + unprot
        keep_rows.sort(key=lambda pe: int(pe[0].get("campaign_rank") or pe[0].get("post_rank") or 999))

    # Rebuild pack with fresh ranks; upgrade thin display hooks when possible
    final_pack: List[Dict[str, Any]] = []
    for i, (p, e) in enumerate(keep_rows, 1):
        row = _maybe_upgrade_hook_fields(p)
        # final safety: if still thin after upgrade, skip (should be rare)
        if _is_thin_hook_raw(_hook_text(row)) and not e.get("protected"):
            e = dict(e)
            e["cut"] = True
            e["decision"] = "cut"
            e["reason"] = "CUT:thin_hook_final"
            cut_rows.append((p, e))
            continue
        if _is_thin_hook_raw(row.get("hook") or "") and not _is_thin_hook_raw(_hook_text(row)):
            row["hook"] = _hook_text(row)
        row["campaign_rank"] = i
        row["post_rank"] = i
        row["marketer_decision"] = e.get("reason")
        row["marketer_protected"] = bool(e.get("protected"))
        final_pack.append(row)
    # re-number if any final skips
    for i, row in enumerate(final_pack, 1):
        row["campaign_rank"] = i
        row["post_rank"] = i

    cut_list = []
    for p, e in cut_rows:
        cut_list.append(
            {
                "episode": p.get("episode"),
                "old_rank": p.get("campaign_rank") or p.get("post_rank"),
                "series_global_score": _global(p),
                "overall_score": _f(p.get("overall_score")),
                "hook": _hook_text(p)[:100],
                "reason": e.get("reason"),
                "fails": e.get("fails"),
                "promo_types": p.get("promo_types"),
            }
        )

    # sort cut list by old rank
    cut_list.sort(key=lambda x: (x.get("old_rank") is None, x.get("old_rank") or 999))

    return {
        "campaign_pack": final_pack,
        "cut_list": cut_list,
        "kept": len(final_pack),
        "cut_count": len(cut_list),
        "protected_count": sum(1 for _, e in keep_rows if e.get("protected")),
        "min_keep": min_keep,
        "max_keep": max_keep,
        "marketer_log": logs,
        "marketer_note": (
            "Marketer agent trims weak hooks/segments/low clarity without removing "
            f"protected promos (top {PROTECT_TOP_K}, global>={PROTECT_GLOBAL}, "
            "strong craft). promo_types never decide keep/cut."
        ),
    }


def optional_llm_borderline_review(
    borderline: List[Dict[str, Any]],
    continuity_one_liner: str = "",
) -> List[Dict[str, Any]]:
    """Optional LLM pass for borderline items only. Safe no-op if no API.

    Returns list of {episode, hook, llm_vote: keep|cut, reason}.
    """
    if not borderline:
        return []
    try:
        from src.llm_agents import call_groq_async
        import asyncio
    except Exception:
        return []

    # Keep prompt tiny — only borderline
    cards = []
    for p in borderline[:12]:
        cards.append(
            {
                "episode": p.get("episode"),
                "hook": _hook_text(p)[:120],
                "cliffhanger": _cliff_text(p)[:120],
                "duration_sec": p.get("duration_sec"),
                "overall_score": p.get("overall_score"),
                "global": _global(p),
            }
        )

    prompt = f"""You are a short-form video marketer for a romantic drama series.
Series: {continuity_one_liner[:300]}

For each promo card, vote KEEP or CUT for a paid/organic cold-traffic pack.
CUT only if hook is empty/address-only, story is unclear, or no open loop.
KEEP strong emotional/conflict/revelation hooks even if late-arc.
Never rank by type label.

Cards JSON:
{json.dumps(cards, ensure_ascii=False)}

Return JSON only:
{{"votes":[{{"episode":1,"hook_prefix":"first 20 chars","vote":"KEEP|CUT","reason":"short"}}]}}
"""

    async def _run():
        try:
            return await call_groq_async(prompt)
        except Exception:
            return None

    try:
        raw = asyncio.get_event_loop().run_until_complete(_run())
    except RuntimeError:
        raw = asyncio.run(_run())
    except Exception:
        return []

    if not raw:
        return []
    try:
        if isinstance(raw, str):
            # extract json
            m = re.search(r"\{.*\}", raw, re.S)
            data = json.loads(m.group(0) if m else raw)
        else:
            data = raw
        return data.get("votes") or []
    except Exception:
        return []


def run_marketer_agent(
    pack: List[Dict[str, Any]],
    min_keep: int = 12,
    max_keep: int = 24,
    target_keep: Optional[int] = None,
    use_llm: bool = False,
    continuity_one_liner: str = "",
) -> Dict[str, Any]:
    """Public entry: deterministic trim (+ optional LLM on borderline)."""
    result = marketer_trim_pack(
        pack,
        min_keep=min_keep,
        max_keep=max_keep,
        target_keep=target_keep,
    )

    if use_llm:
        # Borderline = kept unprotected with any fails/soft flags
        borderline = []
        log_by_hook = {(L.get("episode"), L.get("hook_preview")): L for L in result["marketer_log"]}
        for p in result["campaign_pack"]:
            if p.get("marketer_protected"):
                continue
            key = (p.get("episode"), _hook_text(p)[:80])
            L = log_by_hook.get(key) or {}
            if L.get("fails") or L.get("soft_flags"):
                borderline.append(p)
        votes = optional_llm_borderline_review(borderline, continuity_one_liner)
        result["llm_votes"] = votes
        # Apply CUT votes only on non-protected
        if votes:
            cut_hooks = set()
            for v in votes:
                if str(v.get("vote", "")).upper() == "CUT":
                    cut_hooks.add((int(v.get("episode") or 0), str(v.get("hook_prefix") or "")[:20]))
            new_pack = []
            extra_cuts = []
            for p in result["campaign_pack"]:
                if p.get("marketer_protected"):
                    new_pack.append(p)
                    continue
                pref = _hook_text(p)[:20]
                ep = int(p.get("episode") or 0)
                if (ep, pref) in cut_hooks and len(new_pack) + (len(result["campaign_pack"]) - len(new_pack) - 1) >= min_keep:
                    extra_cuts.append(
                        {
                            "episode": ep,
                            "old_rank": p.get("campaign_rank"),
                            "series_global_score": _global(p),
                            "overall_score": _f(p.get("overall_score")),
                            "hook": _hook_text(p)[:100],
                            "reason": "CUT:llm_marketer",
                            "fails": ["llm_vote"],
                            "promo_types": p.get("promo_types"),
                        }
                    )
                else:
                    new_pack.append(p)
            # re-rank
            for i, p in enumerate(new_pack, 1):
                p["campaign_rank"] = i
                p["post_rank"] = i
            result["campaign_pack"] = new_pack
            result["cut_list"] = (result.get("cut_list") or []) + extra_cuts
            result["kept"] = len(new_pack)
            result["cut_count"] = len(result["cut_list"])

    return result
