"""Mini-Arc Validation - Step 3

Validates whether a story window forms a complete mini-arc (hook → escalation → cliffhanger).

Supports 3 modes:
- rule    : Fast, cheap, heuristic-based
- llm     : High quality, uses LLM
- hybrid  : Rule-based first, LLM only on uncertain cases (recommended)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from src.schemas import Scene, Beat
from src.promo_schemas import StoryPromoCandidate, MiniArcMode


def _rule_based_validation(candidate: StoryPromoCandidate, scenes: List[Scene]) -> Tuple[bool, str]:
    """Fast rule-based check for mini-arc completeness."""
    duration = candidate.duration_sec
    # Prefer full window text; fall back to trigger snippet
    text = (getattr(candidate, "window_text", None) or candidate.trigger_text or "").lower()

    score = 0.0
    reasons = []

    # Duration check (core requirement)
    if 15 <= duration <= 70:
        score += 0.35
        reasons.append("good duration")
    elif duration > 90:
        reasons.append("too long")
        return False, "too long, no clear sub-window"
    elif duration >= 10:
        score += 0.15
        reasons.append("short duration")

    # Strong trigger / emotional language
    strong_triggers = [
        "disown", "never", "get out", "over my", "betray", "end", "swear",
        "from this day", "hate", "love", "leave", "sorry", "please", "won't",
        "inheritance", "mother", "father", "liar", "truth", "hurt"
    ]
    if any(t in text for t in strong_triggers):
        score += 0.3
        reasons.append("strong trigger language")

    # Has some length and emotional weight
    if len(text) > 60:
        score += 0.2
        reasons.append("substantial dialogue")

    # Check if it starts with a hook (first chunk feels dramatic)
    if any(word in text[:80] for word in ["you", "how", "what", "i will", "you are", "don't", "stop"]):
        score += 0.15
        reasons.append("opens with hook")

    # Cliff / open-loop signal
    if "?" in text or any(w in text for w in ["wait", "or else", "i swear", "tell me", "promise"]):
        score += 0.1
        reasons.append("cliffhanger signal")

    is_valid = score >= 0.40
    reason = " | ".join(reasons) if reasons else "weak signals"

    return is_valid, reason


async def _llm_validation(candidate: StoryPromoCandidate, client) -> Tuple[bool, str]:
    """LLM-based mini-arc validation."""
    prompt = f"""You are a professional drama editor.

Does this clip form a **complete mini-story** (has a hook, some escalation, and a clear ending/cliffhanger)?

Clip:
- Duration: {candidate.duration_sec}s
- Trigger line: "{candidate.trigger_text}"
- Window text: "{(getattr(candidate, 'window_text', None) or candidate.trigger_text or '')[:600]}"

Answer ONLY in this format:
VALID: yes/no
REASON: one short sentence"""

    try:
        response = await client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=80
        )
        text = response.choices[0].message.content.strip()

        valid = "yes" in text.split("VALID:")[-1].lower() if "VALID:" in text else False
        reason = text.split("REASON:")[-1].strip() if "REASON:" in text else "LLM unclear"
        return valid, reason
    except Exception as e:
        return False, f"LLM error: {str(e)}"


async def validate_mini_arc(
    candidate: StoryPromoCandidate,
    scenes: List[Scene],
    mode: MiniArcMode,
    llm_client=None
) -> StoryPromoCandidate:
    """Main validation function. Updates candidate in place."""

    if mode == MiniArcMode.RULE:
        valid, reason = _rule_based_validation(candidate, scenes)
        candidate.mini_arc_valid = valid
        candidate.mini_arc_mode = "rule"
        candidate.mini_arc_reason = reason

    elif mode == MiniArcMode.LLM:
        if llm_client is None:
            valid, reason = _rule_based_validation(candidate, scenes)
        else:
            valid, reason = await _llm_validation(candidate, llm_client)
        candidate.mini_arc_valid = valid
        candidate.mini_arc_mode = "llm"
        candidate.mini_arc_reason = reason

    elif mode == MiniArcMode.HYBRID:
        # Rule first; only escalate to LLM when rule rejects (save borderline clips)
        valid, reason = _rule_based_validation(candidate, scenes)
        if valid or llm_client is None:
            candidate.mini_arc_valid = valid
            candidate.mini_arc_reason = f"rule: {reason}"
            candidate.mini_arc_mode = "hybrid"
        else:
            llm_valid, llm_reason = await _llm_validation(candidate, llm_client)
            candidate.mini_arc_valid = llm_valid
            candidate.mini_arc_reason = f"hybrid: rule failed ({reason}) → LLM: {llm_reason}"
            candidate.mini_arc_mode = "hybrid"

    return candidate


async def validate_candidates(
    candidates: List[StoryPromoCandidate],
    episodes: List[Any],
    mode: MiniArcMode = MiniArcMode.HYBRID,
    llm_client=None
) -> List[StoryPromoCandidate]:
    """Validate a list of candidates."""
    validated = []
    for cand in candidates:
        # Find the relevant scenes for this episode
        ep_scenes = []
        for ep in episodes:
            if ep.number == cand.episode:
                ep_scenes = ep.scenes
                break

        updated = await validate_mini_arc(cand, ep_scenes, mode, llm_client)
        if updated.mini_arc_valid:
            validated.append(updated)
    return validated