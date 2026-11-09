"""LLM Specialist Agents for Promo Detection.

Names chosen to match real roles in storytelling & filmmaking:
- PlacementScout   : Finds potential promo moments (like a Product Placement Coordinator)
- NarrativeEditor  : Protects story flow and immersion (like a Script Editor / Continuity Supervisor)
- BrandFitReviewer : Evaluates how naturally a brand integrates (like a Brand Integration Consultant)
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from groq import AsyncGroq

from src.promo_schemas import PromoCandidate, StoryPromoCandidate
import re

# Load environment
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Model to use (fast + cheap)
# Primary + fallback (separate quotas help when TPD is exhausted on one model)
MODEL = "qwen/qwen3.8-27b"
MODEL_FALLBACK = "openai/gpt-oss-20b"

# Concurrency control for free tier
MAX_CONCURRENT = 6
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)


# =============================================================================
# Context Window Configuration (Experiment v1)
# =============================================================================

CONTEXT_WINDOWS = {
    "scene_context": {"before": 3, "after": 2},      # SceneContextAgent
    "luxury_signal": {"before": 1, "after": 0},      # LuxurySignalAgent
    "immersion_risk": {"before": 2, "after": 3},     # ImmersionRiskAgent
}


def get_context_window(beats: List[Dict], current_idx: int, window_type: str) -> List[Dict]:
    """Extract beats within the configured context window."""
    cfg = CONTEXT_WINDOWS.get(window_type, {"before": 2, "after": 2})
    start = max(0, current_idx - cfg["before"])
    end = min(len(beats), current_idx + cfg["after"] + 1)
    return beats[start:end]


# =============================================================================
# Rule-Based Fallback Scorer (used when no LLM client is available)
# =============================================================================

def _clamp_0_10(val) -> float:
    """Normalize a metric that may arrive as 0-1 or 0-10 onto a 0-10 scale."""
    if val is None:
        return 0.0
    try:
        v = float(val)
    except (TypeError, ValueError):
        return 0.0
    if v < 0:
        return 0.0
    # Heuristic: values in (0, 1.5] were almost certainly 0-1 scale
    if 0 < v <= 1.5:
        v = v * 10.0
    return round(min(10.0, max(0.0, v)), 2)


def _rule_based_score_candidate(candidate: StoryPromoCandidate) -> StoryPromoCandidate:
    """Deterministic fallback scoring when no LLM client is provided.

    All criteria use a **0-10** scale (same as the LLM scorer).
    Prefers full window_text over the trigger snippet.
    """
    text = (getattr(candidate, "window_text", None) or candidate.trigger_text or "")
    duration = candidate.duration_sec or 30.0
    words = text.split()
    word_count = len(words)
    text_lower = text.lower()

    hook_strength = 5.0
    cliffhanger_strength = 5.0
    emotional_escalation = 5.0
    narrative_completeness = 6.0
    pacing = 7.0
    dialogue_impact = 5.0

    # === Hook Strength ===
    strong_starters = [
        "i will not", "you are no", "how dare", "get out", "over my dead",
        "from now on", "this is the end", "i swear", "you betrayed", "disown",
        "i love you", "don't die", "stay with me", "you are my father",
    ]
    if any(text_lower.startswith(s) or s in text_lower[:50] for s in strong_starters):
        hook_strength = 8.5
    elif "?" in text[:80]:
        hook_strength = 7.5
    elif word_count <= 12 and word_count >= 3:
        hook_strength = 7.0
    elif any(w in text_lower for w in ["you", "what", "how", "never", "kiss", "blood"]):
        hook_strength = 6.5

    # === Cliffhanger Strength ===
    cliff_markers = [
        "never", "dead to me", "regret", "over my dead", "this is the end",
        "you will never", "mark my words", "i refuse", "or else", "i swear",
        "don't die", "i love you", "promise me", "stay with me",
    ]
    if any(m in text_lower for m in cliff_markers):
        cliffhanger_strength = 8.2
    if "!" in text or "..." in text or "?" in text:
        cliffhanger_strength = min(9.0, cliffhanger_strength + 1.0)

    # === Emotional Escalation ===
    if any(w in text_lower for w in [
        "furious", "devastated", "betray", "disown", "heartbroken", "hate",
        "love", "blood", "wound", "kiss", "trembling",
    ]):
        emotional_escalation = 8.5
    elif any(w in text_lower for w in ["angry", "shocked", "swear", "hurt", "sorry", "please", "scared"]):
        emotional_escalation = 7.2

    # === Narrative Completeness ===
    if 15 <= word_count <= 160:
        narrative_completeness = 7.8
    if 15 <= duration <= 70:
        narrative_completeness = min(8.5, narrative_completeness + 1.0)

    # === Pacing ===
    if 15 <= duration <= 55:
        pacing = 8.5
    elif duration > 70:
        pacing = 4.5
    elif duration < 12:
        pacing = 5.0

    # === Dialogue Impact ===
    punchy = ["i will not", "you are no", "how dare", "disown", "i love you", "don't die"]
    if word_count <= 24 and any(p in text_lower for p in punchy):
        dialogue_impact = 8.8
    elif "!" in text or word_count >= 10:
        dialogue_impact = 7.5

    overall = (
        hook_strength * 0.20 +
        cliffhanger_strength * 0.22 +
        emotional_escalation * 0.18 +
        narrative_completeness * 0.15 +
        pacing * 0.12 +
        dialogue_impact * 0.13
    )

    candidate.hook_strength = round(hook_strength, 2)
    candidate.cliffhanger_strength = round(cliffhanger_strength, 2)
    candidate.emotional_escalation = round(emotional_escalation, 2)
    candidate.narrative_completeness = round(narrative_completeness, 2)
    candidate.pacing = round(pacing, 2)
    candidate.dialogue_impact = round(dialogue_impact, 2)
    candidate.overall_score = round(overall, 2)
    candidate.llm_rationale = (
        f"Rule-based score={candidate.overall_score}/10 "
        f"(hook={hook_strength:.1f}, cliff={cliffhanger_strength:.1f})"
    )

    promo_types = []
    if emotional_escalation >= 7.0:
        promo_types.append("emotional")
    if cliffhanger_strength >= 7.0:
        promo_types.append("cliffhanger")
    if hook_strength >= 7.0:
        promo_types.append("revelation")
    if any(w in text_lower for w in ["kiss", "love", "embrace", "tender"]):
        promo_types.append("romantic")
    if any(w in text_lower for w in ["blood", "wound", "kill", "revenge"]):
        promo_types.append("thrilling")
    if not promo_types:
        promo_types = ["conflict"]
    candidate.promo_types = promo_types

    return candidate


# =============================================================================
# Hybrid Scoring (Rule-Based + LLM Refinement)
# =============================================================================

HYBRID_REFINEMENT_PROMPT = """You are a senior drama promo strategist.

Given this promo candidate that was already scored by rules, refine ONLY the following:
- Suggest the best `hook_type` from: mystery, emotional, conflict, revelation, action, none
- Write a one-sentence `reason` explaining why this moment works as a promo
- Optionally suggest additional `promo_types` if the rule-based ones missed something

Return ONLY valid JSON:
{
  "hook_type": "...",
  "reason": "...",
  "promo_types": ["..."]
}

Trigger Text: {trigger}
Duration: {duration}s
Current Scores: hook={hook}, cliff={cliff}, emotion={emotion}
Current Promo Types: {types}"""


async def _chat_json(client, prompt: str, max_tokens: int = 300) -> dict:
    """Shared chat → JSON helper with model fallback + light rate-limit retry."""
    last_err = None
    model_idx = 0
    models = [MODEL, MODEL_FALLBACK]
    for attempt in range(4):
        model = models[min(model_idx, len(models) - 1)]
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=max_tokens,
            )
            content = (response.choices[0].message.content or "").strip()
            content = re.sub(r"```json|```", "", content).strip()
            m = re.search(r"\{[\s\S]*\}", content)
            return json.loads(m.group(0) if m else content)
        except Exception as e:
            last_err = e
            msg = str(e)
            if "tokens per day" in msg.lower() or "TPD" in msg:
                if model_idx < len(models) - 1:
                    model_idx += 1
                    continue
                raise
            if "429" in msg or "rate" in msg.lower():
                await asyncio.sleep(min(5.0, 1.0 * (2 ** attempt)))
                continue
            if model_idx < len(models) - 1:
                model_idx += 1
                continue
            raise last_err
    raise last_err or RuntimeError("chat_json failed")


async def hybrid_score_candidate(candidate: StoryPromoCandidate, client) -> StoryPromoCandidate:
    """Hybrid scoring: Rule-based first, then LLM refinement for hook_type + reason."""
    candidate = _rule_based_score_candidate(candidate)

    if client is None:
        return candidate

    try:
        prompt = HYBRID_REFINEMENT_PROMPT.format(
            trigger=(getattr(candidate, "window_text", None) or candidate.trigger_text or "")[:800],
            duration=candidate.duration_sec,
            hook=candidate.hook_strength,
            cliff=candidate.cliffhanger_strength,
            emotion=candidate.emotional_escalation,
            types=candidate.promo_types or [],
        )
        data = await _chat_json(client, prompt, max_tokens=200)
        if data.get("hook_type"):
            candidate.hook_type = data["hook_type"]
        if data.get("reason"):
            candidate.reason = data["reason"]
            candidate.llm_rationale = data["reason"]
        if data.get("promo_types"):
            existing = set(candidate.promo_types or [])
            existing.update(data["promo_types"])
            candidate.promo_types = list(existing)
    except Exception:
        pass

    return candidate


def format_beats_for_prompt(beats: List[Dict], current_idx_in_window: int) -> str:
    """Format beats as readable context for the LLM."""
    lines = []
    for i, beat in enumerate(beats):
        marker = ">>> " if i == current_idx_in_window else "    "
        char = beat.get("character", "Unknown")
        text = beat.get("text", "")
        lines.append(f"{marker}[{char}] {text}")
    return "\n".join(lines)


# =============================================================================
# Agent Prompts
# =============================================================================

SCENE_CONTEXT_PROMPT = """You are a Scene Context Analyst for a TV drama.

Your job: Analyze the emotional tone, pacing, and narrative purpose of the CURRENT beat within its surrounding context.

Episode Logline: {logline}

Context Beats:
{context}

Respond ONLY with valid JSON:
{{
  "tone": "one of [intimate, tense, romantic, melancholic, hopeful, dramatic, quiet]",
  "pacing": "one of [slow, medium, fast]",
  "scene_purpose": "short description of what this scene is doing narratively",
  "mood_shift": "true/false - does the current beat show a clear mood shift?",
  "confidence": 0.0-1.0
}}"""

LUXURY_SIGNAL_PROMPT = """You are a Luxury Brand Signal Detector.

Your job: Detect if the CURRENT beat contains natural opportunities for luxury brand placement (fashion, jewelry, travel, lifestyle).

Episode Logline: {logline}

Context Beats:
{context}

Respond ONLY with valid JSON:
{{
  "has_luxury_signal": true/false,
  "signal_strength": 0.0-1.0,
  "detected_category": "fashion|jewelry|travel|lifestyle|none",
  "reason": "one sentence explaining the signal or lack thereof",
  "natural_mention": true/false - would a brand mention feel natural here?
}}"""

IMMERSION_RISK_PROMPT = """You are a Narrative Immersion Guardian.

Your job: Evaluate whether inserting a brand mention at the CURRENT beat would break viewer immersion or feel forced.

Episode Logline: {logline}

Context Beats:
{context}

Respond ONLY with valid JSON:
{{
  "immersion_risk": 0.0-1.0,
  "risk_level": "low|medium|high",
  "reason": "one sentence explaining the risk",
  "timing_appropriate": true/false - is this moment emotionally/temporally suitable for a subtle brand mention?
}}"""


# =============================================================================
# Hook & Cliffhanger Prompts (for 20-60s Promo Optimization)
# =============================================================================

HOOK_STRENGTH_PROMPT = """You are a Promo Hook Analyst.

Your job: Evaluate how strong the OPENING of this scene window is as a hook for a 20-60 second promo.

A great hook should:
- Grab attention immediately (mystery, emotion, conflict, or high stakes)
- Make the viewer want to keep watching
- Work well as the first 3-8 seconds of a short promo

Episode Logline: {logline}

Opening Beats (first 20-30% of window):
{context}

Respond ONLY with valid JSON:
{{
  "hook_strength": 0.0-1.0,
  "hook_type": "mystery|emotional|conflict|revelation|action|none",
  "reason": "one sentence explaining why this is or isn't a strong hook"
}}"""


CLIFFHANGER_STRENGTH_PROMPT = """You are a Promo Cliffhanger Analyst.

Your job: Evaluate how strong the ENDING of this scene window is as a cliffhanger/tease for a 20-60 second promo.

A great cliffhanger should:
- Leave the viewer wanting more (unresolved tension, shocking reveal, emotional peak)
- Make them curious about what happens next
- Work perfectly as the final 3-8 seconds of a short promo

Episode Logline: {logline}

Closing Beats (last 20-30% of window):
{context}

Respond ONLY with valid JSON:
{{
  "cliffhanger_strength": 0.0-1.0,
  "cliffhanger_type": "revelation|emotional_peak|danger|twist|question|none",
  "reason": "one sentence explaining the cliffhanger quality"
}}"""


EMOTIONAL_PEAK_PROMPT = """You are an Emotional Intensity Analyst.

Your job: Rate the emotional intensity/peak of this scene window for a short promo.

A high emotional peak (0.8-1.0) means strong feelings — heartbreak, rage, joy, fear, love, betrayal.
Low intensity (0.0-0.4) means flat, neutral, or purely functional dialogue.

Episode Logline: {logline}

Scene Beats:
{context}

Respond ONLY with valid JSON:
{{
  "emotional_intensity": 0.0-1.0,
  "dominant_emotion": "love|anger|fear|joy|sadness|betrayal|none",
  "reason": "one sentence"
}}"""


PACING_PROMPT = """You are a Promo Pacing Analyst.

Your job: Evaluate if this scene window has good pacing and rhythm for a 20-60 second promo.

Good pacing for short promos: tight, dynamic, not too slow or too talky. Should feel snappy when cut to 20-60s.

Episode Logline: {logline}

Scene Beats:
{context}

Respond ONLY with valid JSON:
{{
  "pacing_score": 0.0-1.0,
  "pacing_type": "tight|dynamic|talky|slow|balanced",
  "reason": "one sentence"
}}"""


TENSION_PROMPT = """You are a Narrative Tension Analyst.

Your job: Rate the level of tension, conflict, or stakes in this scene window.

High tension = conflict, danger, argument, high stakes, suspense.
Low tension = calm, peaceful, low-stakes conversation.

Episode Logline: {logline}

Scene Beats:
{context}

Respond ONLY with valid JSON:
{{
  "tension_score": 0.0-1.0,
  "tension_type": "conflict|danger|suspense|emotional|low",
  "reason": "one sentence"
}}"""


# =============================================================================
# LLM Call Helpers (Async)
# =============================================================================

async def call_groq_async(prompt: str, temperature: float = 0.2) -> Dict[str, Any]:
    """Async call to Groq with rate limiting."""
    if not async_client:
        return {"error": "No Groq client configured"}

    async with _semaphore:
        try:
            response = await async_client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                response_format={"type": "json_object"},
                max_tokens=400,
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {"error": str(e)}


# =============================================================================
# Specialized Agents (Real LLM versions)
# =============================================================================

def _get_relative_index(window: List[Dict], beats: List[Dict], current_idx: int) -> int:
    """Find the position of the current beat inside the window."""
    if not window:
        return 0
    for i, b in enumerate(window):
        if b is beats[current_idx] or (b.get("text") == beats[current_idx].get("text")):
            return i
    return min(len(window) // 2, len(window) - 1)


async def scene_context_agent(beats: List[Dict], current_idx: int, logline: str) -> Dict[str, Any]:
    """Analyzes scene tone and context."""
    window = get_context_window(beats, current_idx, "scene_context")
    rel_idx = _get_relative_index(window, beats, current_idx)
    context_text = format_beats_for_prompt(window, rel_idx)
    prompt = SCENE_CONTEXT_PROMPT.format(logline=logline, context=context_text)
    return await call_groq_async(prompt)


async def luxury_signal_agent(beats: List[Dict], current_idx: int, logline: str) -> Dict[str, Any]:
    """Detects luxury/brand placement signals."""
    window = get_context_window(beats, current_idx, "luxury_signal")
    rel_idx = _get_relative_index(window, beats, current_idx)
    context_text = format_beats_for_prompt(window, rel_idx)
    prompt = LUXURY_SIGNAL_PROMPT.format(logline=logline, context=context_text)
    return await call_groq_async(prompt)


async def immersion_risk_agent(beats: List[Dict], current_idx: int, logline: str) -> Dict[str, Any]:
    """Evaluates immersion risk for brand insertion."""
    window = get_context_window(beats, current_idx, "immersion_risk")
    rel_idx = _get_relative_index(window, beats, current_idx)
    context_text = format_beats_for_prompt(window, rel_idx)
    prompt = IMMERSION_RISK_PROMPT.format(logline=logline, context=context_text)
    return await call_groq_async(prompt)


async def hook_strength_agent(beats: List[Dict], current_idx: int, logline: str) -> Dict[str, Any]:
    """Evaluates how strong the opening of the candidate window is as a promo hook."""
    window = get_context_window(beats, current_idx, "hook")
    # Use first 30% of window as "opening"
    opening_size = max(2, len(window) // 3)
    opening = window[:opening_size]
    context_text = format_beats_for_prompt(opening, 0)
    prompt = HOOK_STRENGTH_PROMPT.format(logline=logline, context=context_text)
    return await call_groq_async(prompt)


async def cliffhanger_strength_agent(beats: List[Dict], current_idx: int, logline: str) -> Dict[str, Any]:
    """Evaluates how strong the ending of the candidate window is as a promo cliffhanger."""
    window = get_context_window(beats, current_idx, "cliffhanger")
    # Use last 30% of window as "closing"
    closing_size = max(2, len(window) // 3)
    closing = window[-closing_size:]
    context_text = format_beats_for_prompt(closing, len(closing) - 1)
    prompt = CLIFFHANGER_STRENGTH_PROMPT.format(logline=logline, context=context_text)
    return await call_groq_async(prompt)


async def emotional_peak_agent(beats: List[Dict], current_idx: int, logline: str) -> Dict[str, Any]:
    """Rates emotional intensity of the scene window."""
    window = get_context_window(beats, current_idx, "emotion")
    context_text = format_beats_for_prompt(window, len(window) // 2)
    prompt = EMOTIONAL_PEAK_PROMPT.format(logline=logline, context=context_text)
    return await call_groq_async(prompt)


async def pacing_agent(beats: List[Dict], current_idx: int, logline: str) -> Dict[str, Any]:
    """Evaluates pacing suitability for a short 20-60s promo."""
    window = get_context_window(beats, current_idx, "pacing")
    context_text = format_beats_for_prompt(window, len(window) // 2)
    prompt = PACING_PROMPT.format(logline=logline, context=context_text)
    return await call_groq_async(prompt)


async def tension_agent(beats: List[Dict], current_idx: int, logline: str) -> Dict[str, Any]:
    """Rates tension/conflict level in the scene."""
    window = get_context_window(beats, current_idx, "tension")
    context_text = format_beats_for_prompt(window, len(window) // 2)
    prompt = TENSION_PROMPT.format(logline=logline, context=context_text)
    return await call_groq_async(prompt)


# =============================================================================
# Character–Brand Affinity Matrix
# =============================================================================

# Lightweight affinity knowledge base
# Format: (character_lower, luxury_keywords) -> affinity_score (0.0 to 1.0)
CHARACTER_BRAND_AFFINITY = {
    # Juliana (female lead, romantic, elegant, wedding context)
    ("juliana", "ring"): 0.95,
    ("juliana", "wedding"): 0.92,
    ("juliana", "gown"): 0.90,
    ("juliana", "dress"): 0.85,
    ("juliana", "jewelry"): 0.88,
    ("juliana", "necklace"): 0.87,
    ("juliana", "bracelet"): 0.82,
    ("juliana", "earring"): 0.80,
    ("juliana", "watch"): 0.65,
    ("juliana", "perfume"): 0.78,
    ("juliana", "handbag"): 0.75,
    ("juliana", "shoe"): 0.70,

    # Mysterious Bearded Man (male, mysterious, rugged elegance)
    ("mysterious bearded man", "ring"): 0.75,
    ("mysterious bearded man", "watch"): 0.85,
    ("mysterious bearded man", "cufflink"): 0.80,
    ("mysterious bearded man", "leather"): 0.82,
    ("mysterious bearded man", "whiskey"): 0.70,
    ("mysterious bearded man", "perfume"): 0.60,

    # Default fallback
    ("default", "ring"): 0.60,
    ("default", "watch"): 0.55,
    ("default", "jewelry"): 0.50,
}


def compute_character_brand_affinity(beat: Dict, luxury_item: str = "") -> float:
    """
    Compute how naturally a luxury item fits a character in this moment.
    Returns affinity score between 0.0 and 1.0.
    """
    if not beat or not luxury_item:
        return 0.55  # neutral default

    char = str(beat.get("character", "")).lower().strip()
    item = luxury_item.lower()

    # Try exact character match
    for (c, keyword), score in CHARACTER_BRAND_AFFINITY.items():
        if c == char and keyword in item:
            return score

    # Try partial character match
    for (c, keyword), score in CHARACTER_BRAND_AFFINITY.items():
        if c != "default" and c in char and keyword in item:
            return score

    # Fallback to default item affinity or neutral
    for (c, keyword), score in CHARACTER_BRAND_AFFINITY.items():
        if c == "default" and keyword in item:
            return score

    return 0.55  # neutral if nothing matches


# =============================================================================
# Main Orchestration (Async + Parallel)
# =============================================================================

async def enrich_candidate_async(
    candidate: PromoCandidate,
    logline: str = "",
    all_beats: Optional[List[Dict]] = None,
    current_idx: Optional[int] = None
) -> PromoCandidate:
    """
    Run all three agents in parallel on a single candidate.
    Requires `all_beats` + `current_idx` for proper context windows.
    """
    if not async_client:
        # No key → return neutral score
        candidate.llm_score = 0.5
        candidate.final_score = 0.5
        candidate.llm_reason = "No Groq key configured"
        return candidate

    if all_beats is None or current_idx is None:
        # Fallback without context
        scene_ctx = {"tone": "neutral", "confidence": 0.5}
        luxury_sig = {"has_luxury_signal": True, "signal_strength": 0.55, "reason": "No context"}
        immersion = {"immersion_risk": 0.45, "risk_level": "medium"}
        hook = {"hook_strength": 0.5, "hook_type": "none"}
        cliff = {"cliffhanger_strength": 0.5, "cliffhanger_type": "none"}
        emotion = {"emotional_intensity": 0.5}
        pacing = {"pacing_score": 0.6}
        tension = {"tension_score": 0.5}
        duration_score = 0.6
    else:
        # Run all agents in parallel (now 8 agents total)
        scene_ctx, luxury_sig, immersion, hook, cliff, emotion, pacing, tension = await asyncio.gather(
            scene_context_agent(all_beats, current_idx, logline),
            luxury_signal_agent(all_beats, current_idx, logline),
            immersion_risk_agent(all_beats, current_idx, logline),
            hook_strength_agent(all_beats, current_idx, logline),
            cliffhanger_strength_agent(all_beats, current_idx, logline),
            emotional_peak_agent(all_beats, current_idx, logline),
            pacing_agent(all_beats, current_idx, logline),
            tension_agent(all_beats, current_idx, logline),
        )

        # Duration fit (20-60s ideal for promo)
        duration_sec = getattr(candidate, "duration_sec", None)
        if duration_sec is None and hasattr(candidate, "start_sec") and hasattr(candidate, "end_sec"):
            duration_sec = candidate.end_sec - candidate.start_sec
        if duration_sec:
            if 20 <= duration_sec <= 60:
                duration_score = 1.0
            elif 15 <= duration_sec < 20 or 60 < duration_sec <= 75:
                duration_score = 0.7
            else:
                duration_score = 0.3
        else:
            duration_score = 0.6

    # Weighted scoring — PRIORITIZING HOOK + CLIFFHANGER for 20-60s promos
    luxury_score = luxury_sig.get("signal_strength", 0.5) if luxury_sig.get("has_luxury_signal") else 0.25
    immersion_score = 1.0 - immersion.get("immersion_risk", 0.5)
    scene_conf = scene_ctx.get("confidence", 0.6)
    hook_score = hook.get("hook_strength", 0.5)
    cliff_score = cliff.get("cliffhanger_strength", 0.5)
    emotion_score = emotion.get("emotional_intensity", 0.5)
    pacing_score = pacing.get("pacing_score", 0.6)
    tension_score = tension.get("tension_score", 0.5)

    # Character–Brand Affinity
    current_beat = all_beats[current_idx] if 0 <= current_idx < len(all_beats) else {}
    detected_brand = luxury_sig.get("detected_brand", "") or luxury_sig.get("reason", "")
    affinity_score = compute_character_brand_affinity(current_beat, detected_brand)

    # === IMPROVED SCORING FOR 20-60s PROMOS (Hook + Cliffhanger focus) ===

    # Hard penalties: if hook or cliffhanger are weak, the candidate is bad for our goal
    hook_penalty = 0.0 if hook_score >= 0.38 else (0.38 - hook_score) * 0.6
    cliff_penalty = 0.0 if cliff_score >= 0.38 else (0.38 - cliff_score) * 0.6

    # Big bonus when BOTH hook and cliffhanger are strong (ideal promo structure)
    structure_bonus = 0.0
    if hook_score >= 0.65 and cliff_score >= 0.65:
        structure_bonus = 0.12
    elif hook_score >= 0.55 and cliff_score >= 0.55:
        structure_bonus = 0.06

    # Duration is now a harder requirement (sweet spot 20-60s)
    duration_factor = duration_score if 20 <= (candidate.end_sec - candidate.start_sec) <= 60 else duration_score * 0.4

    # Core weighted score (Hook + Cliffhanger still dominant)
    base_score = (
        0.24 * hook_score +
        0.26 * cliff_score +
        0.11 * immersion_score +
        0.09 * emotion_score +
        0.07 * tension_score +
        0.07 * pacing_score +
        0.07 * duration_factor +
        0.05 * scene_conf +
        0.02 * luxury_score +
        0.02 * affinity_score
    )

    final = round(max(0.0, base_score + structure_bonus - hook_penalty - cliff_penalty), 3)

    candidate.llm_score = final
    candidate.final_score = final
    candidate.llm_reason = (
        f"Hook:{round(hook_score,2)} Cliff:{round(cliff_score,2)} "
        f"Emo:{round(emotion_score,2)} Tens:{round(tension_score,2)} "
        f"Pace:{round(pacing_score,2)} Struct+:{round(structure_bonus,2)}"
    )

    return candidate


async def run_agents_on_candidates_async(
    candidates: List[PromoCandidate],
    loglines: Dict[int, str],
    episodes_data: Dict[int, List[Dict]],
    episode_beat_index: Optional[Dict[Tuple[int, int], int]] = None
) -> List[PromoCandidate]:
    """
    Enrich all candidates with parallel LLM calls.

    episodes_data: {episode_num: [beat_dicts]}
    episode_beat_index: optional precomputed map of (episode, scene) -> beat_index
    """
    tasks = []
    for c in candidates:
        logline = loglines.get(c.episode, "")
        beats = episodes_data.get(c.episode, [])
        idx = c.beat_index if c.beat_index is not None else None
        if idx is not None and (idx < 0 or idx >= len(beats)):
            idx = None
        tasks.append(enrich_candidate_async(c, logline, beats if beats else None, idx))

    return await asyncio.gather(*tasks)


# =============================================================================
# Sync Wrapper (for existing orchestrator code)
# =============================================================================

def run_agents_on_candidates(
    candidates: List[PromoCandidate],
    loglines: Dict[int, str],
    episodes_data: Optional[Dict[int, List[Dict]]] = None
) -> List[PromoCandidate]:
    """
    Sync wrapper. Builds episode data if not provided and runs async pipeline.
    """
    if episodes_data is None:
        episodes_data = {}

    # Build a simple index map
    index_map = {}
    for ep, beats in episodes_data.items():
        for i, b in enumerate(beats):
            if "scene" in b:
                index_map[(ep, b["scene"])] = i

    return asyncio.run(
        run_agents_on_candidates_async(candidates, loglines, episodes_data, index_map)
    )


# ============================================================
# NEW STORYTELLING PROMO AGENTS (Steps 4 & 6)
# ============================================================

SCORING_PROMPT = """You are a senior drama promo editor.

Score this clip on the following criteria (0-10 each):

Clip:
- Duration: {duration}s
- Trigger: "{trigger}"

Criteria:
1. Hook Strength (first 5-7 seconds)
2. Cliffhanger / Ending Impact
3. Emotional Escalation
4. Narrative Completeness
5. Pacing & Rhythm
6. Dialogue Impact / Quotability
7. Character Stakes

Return ONLY valid JSON:
{{
  "hook_strength": X,
  "cliffhanger_strength": X,
  "emotional_escalation": X,
  "narrative_completeness": X,
  "pacing": X,
  "dialogue_impact": X,
  "character_stakes": X,
  "rationale": "one short sentence"
}}"""


TYPE_CLASSIFICATION_PROMPT = """Classify this promo clip into one or more categories.

Clip:
- Duration: {duration}s
- Trigger: "{trigger}"

Possible categories:
- romantic, dramatic, thrilling, revenge, mystery, heroic, dark, witty, family_conflict, betrayal

Return ONLY JSON:
{{
  "promo_types": ["category1", "category2"]
}}"""


async def score_candidate(candidate: StoryPromoCandidate, client=None) -> StoryPromoCandidate:
    """Step 4: Score a candidate using LLM on 7 criteria.
    
    If client is None, falls back to deterministic rule-based scoring.
    """
    if client is None:
        return _rule_based_score_candidate(candidate)

    prompt = SCORING_PROMPT.format(
        duration=candidate.duration_sec,
        trigger=(getattr(candidate, "window_text", None) or candidate.trigger_text or "")[:800],
    )

    last_err = None
    models_to_try = [MODEL, MODEL_FALLBACK]
    model_idx = 0
    for attempt in range(5):
        model = models_to_try[min(model_idx, len(models_to_try) - 1)]
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=450,
            )
            content = (response.choices[0].message.content or "").strip()

            import json as pyjson
            m = re.search(r"\{[\s\S]*\}", content)
            data = pyjson.loads(m.group(0) if m else content)

            candidate.hook_strength = _clamp_0_10(data.get("hook_strength"))
            candidate.cliffhanger_strength = _clamp_0_10(data.get("cliffhanger_strength"))
            candidate.emotional_escalation = _clamp_0_10(data.get("emotional_escalation"))
            candidate.narrative_completeness = _clamp_0_10(data.get("narrative_completeness"))
            candidate.pacing = _clamp_0_10(data.get("pacing"))
            candidate.dialogue_impact = _clamp_0_10(data.get("dialogue_impact"))
            candidate.character_stakes = _clamp_0_10(data.get("character_stakes"))
            candidate.llm_rationale = data.get("rationale", "") or f"scored via {model}"

            weights = {
                "hook_strength": 0.25,
                "cliffhanger_strength": 0.25,
                "emotional_escalation": 0.15,
                "narrative_completeness": 0.15,
                "pacing": 0.10,
                "dialogue_impact": 0.05,
                "character_stakes": 0.05,
            }
            total = 0.0
            for k, w in weights.items():
                val = _clamp_0_10(getattr(candidate, k) or 5.0)
                total += val * w
            candidate.overall_score = round(total, 2)
            return candidate
        except Exception as e:
            last_err = e
            msg = str(e)
            # Daily/token cap on this model → switch model once, then stop
            if "tokens per day" in msg.lower() or "TPD" in msg:
                if model_idx < len(models_to_try) - 1:
                    model_idx += 1
                    continue
                break
            if "429" in msg or "rate" in msg.lower():
                await asyncio.sleep(min(6.0, 1.0 * (2 ** attempt)))
                continue
            # Non-rate errors: try next model once
            if model_idx < len(models_to_try) - 1:
                model_idx += 1
                continue
            break

    candidate = _rule_based_score_candidate(candidate)
    candidate.llm_rationale = f"LLM scoring failed ({last_err}); used rule-based fallback"
    return candidate


async def classify_promo_type(candidate: StoryPromoCandidate, client=None) -> StoryPromoCandidate:
    """Step 6: Classify the type of promo.
    
    If client is None, uses the types already set by the rule-based scorer.
    """
    if client is None:
        # Types already assigned by _rule_based_score_candidate
        return candidate

    prompt = TYPE_CLASSIFICATION_PROMPT.format(
        duration=candidate.duration_sec,
        trigger=candidate.trigger_text
    )

    try:
        response = await client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=60
        )
        content = response.choices[0].message.content.strip()
        import json as pyjson
        data = pyjson.loads(content)
        candidate.promo_types = data.get("promo_types", [])
    except Exception:
        pass  # keep existing types from fallback

    return candidate


async def run_scoring_and_classification(
    candidates: List[StoryPromoCandidate],
    client=None,
    mode: str = "hybrid",
    llm_per_episode: int = 5,
    concurrency: int = 2,
) -> List[StoryPromoCandidate]:
    """
    Run scoring + classification on candidates.

    Modes:
        - "rule"    : Pure rule-based scoring (no LLM needed)
        - "llm"     : Rule pre-score → LLM re-score top-N per episode (parallel)
        - "hybrid"  : Rule score all → LLM refine top-N per episode (types/rationale)

    If client is None, automatically falls back to "rule" mode.

    Speed design:
      1) Always rule-score everything (instant).
      2) Only spend LLM budget on the best `llm_per_episode` per episode.
      3) Parallelize LLM calls with a concurrency cap.
    """
    import asyncio
    from collections import defaultdict

    if client is None:
        mode = "rule"

    # 1) Rule baseline for everyone
    scored: List[StoryPromoCandidate] = []
    for cand in candidates:
        cand = _rule_based_score_candidate(cand)
        scored.append(cand)

    if mode == "rule" or client is None:
        return scored

    # 2) Pick top-N per episode for LLM spend
    by_ep: Dict[int, List[StoryPromoCandidate]] = defaultdict(list)
    for c in scored:
        by_ep[c.episode].append(c)

    llm_targets: List[StoryPromoCandidate] = []
    for ep, lst in by_ep.items():
        ranked = sorted(lst, key=lambda x: x.overall_score or 0, reverse=True)
        llm_targets.extend(ranked[: max(1, llm_per_episode)])

    target_ids = {id(c) for c in llm_targets}
    print(f"  LLM scoring {len(llm_targets)}/{len(scored)} candidates "
          f"(top {llm_per_episode}/ep, concurrency={concurrency})")

    sem = asyncio.Semaphore(concurrency)

    async def _llm_one(cand: StoryPromoCandidate) -> None:
        async with sem:
            try:
                if mode == "llm":
                    # score_candidate already returns 0-10 metrics; skip extra classify call
                    await score_candidate(cand, client=client)
                else:  # hybrid
                    await hybrid_score_candidate(cand, client=client)
            except Exception as e:
                if getattr(cand, "overall_score", None) is None:
                    _rule_based_score_candidate(cand)
                cand.llm_rationale = f"LLM failed ({e}); kept rule score"
            if getattr(cand, "overall_score", None) is None:
                _rule_based_score_candidate(cand)

    # Sequential-ish with small concurrency (gather over targets only)
    targets = [c for c in scored if id(c) in target_ids]
    # Process in small waves to avoid hanging forever on rate limits
    wave = max(1, concurrency)
    for i in range(0, len(targets), wave):
        batch = targets[i : i + wave]
        print(f"  LLM wave {i // wave + 1}/{(len(targets) + wave - 1) // wave} ({len(batch)} clips)")
        await asyncio.gather(*[_llm_one(c) for c in batch])
    return scored