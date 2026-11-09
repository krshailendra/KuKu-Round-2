"""Story Window Expansion - Step 2 of the new promo pipeline.

Generates natural 20-60 second storytelling windows (hook → cliffhanger).
Handles long scenes by finding strong internal sub-windows.

Trigger detection supports three modes:
- rule   : Rich static universal keyword taxonomy + signals
- hybrid : Keywords first, then LLM semantic fallback for borderline beats
- llm    : LLM directly proposes the best dramatic trigger beats
"""

import json
import os
from dataclasses import fields
from typing import List, Dict, Any, Optional
from src.schemas import Episode, Beat, Scene
from src.promo_schemas import StoryPromoCandidate


def _filter_kwargs(cls, data: dict) -> dict:
    allowed = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in allowed}


def _beat_from_dict(d: dict) -> Beat:
    return Beat(**_filter_kwargs(Beat, d))


def _scene_from_dict(d: dict) -> Scene:
    raw = dict(d)
    beats = raw.pop("beats", []) or []
    scene = Scene(**_filter_kwargs(Scene, raw))
    scene.beats = [_beat_from_dict(b) if isinstance(b, dict) else b for b in beats]
    return scene


def load_episodes(processed_dir: str) -> List[Episode]:
    """Load processed episode JSON into nested Beat/Scene/Episode dataclasses."""
    eps = []
    for f in sorted(os.listdir(processed_dir)):
        if f.startswith("ep_") and f.endswith(".json"):
            with open(os.path.join(processed_dir, f), encoding="utf-8") as fh:
                data = json.load(fh)
            raw = dict(data)
            scenes = raw.pop("scenes", []) or []
            ep = Episode(**_filter_kwargs(Episode, raw))
            ep.scenes = [_scene_from_dict(s) if isinstance(s, dict) else s for s in scenes]
            eps.append(ep)
    return eps


# =============================================================================
# UNIVERSAL DRAMATIC TRIGGER TAXONOMY (Generalized, not script-specific)
# =============================================================================

TRIGGER_TAXONOMY = {
    # High-impact: Core dramatic pivots
    "betrayal_disownment": [
        "disown", "betray", "dead to me", "never forgive", "you are no longer",
        "you are not my", "i have no son", "i have no daughter", "you are dead to me",
        "i want nothing to do with you", "consider yourself disowned", "inheritance",
    ],
    "ultimatums_threats": [
        "over my dead body", "if you", "or else", "this is your last chance",
        "swear to god", "mark my words", "you will regret", "this is the last time",
        "choose now", "make your choice", "it's me or", "one more word and",
    ],
    "power_shifts_control": [
        "from now on", "you work for me", "i'm in charge", "things are different now",
        "you answer to me", "i call the shots", "this family is mine", "i decide",
        "you have no say", "i'm taking over",
    ],
    "strong_refusals": [
        "i will not", "i refuse", "not while i'm alive", "over my dead body",
        "i'd rather die", "that will never happen", "i won't allow it",
    ],
    # Medium-impact: Emotional revelations and confrontations
    "revelations_secrets": [
        "i have to tell you", "the truth is", "i lied", "i can't do this anymore",
        "there's something you should know", "i've been hiding", "the real reason",
        "i'm not who you think", "this changes everything", "you are my father",
        "you are my mother", "i am your",
    ],
    "confrontations_accusations": [
        "how dare you", "how could you", "after everything", "i love you but",
        "you betrayed", "you lied to me", "you used me", "i trusted you",
        "get out", "leave this house", "this is the end", "we're done",
    ],
    "emotional_breaks": [
        "i can't", "i won't", "please don't", "i'm begging you", "this is killing me",
        "my heart is breaking", "i have nothing left", "you broke me", "i need you",
        "don't leave me", "stay with me",
    ],
    "finality_closures": [
        "from this day", "you will never", "this is goodbye", "it's over",
        "i'm leaving", "we're finished", "no turning back", "the end of",
    ],
    # Romance / intimacy / peril — needed for soft-drama & romantic episodes
    "romance_intimacy": [
        "kiss", "kissed", "hold me", "in my arms", "closer", "touch me",
        "heartbeat", "breathing", "whisper", "gaze", "trembling", "softly",
        "tender", "caress", "embrace", "lips", "captivat", "his eyes", "her eyes",
        "leaned in", "pulled her", "pulled him", "against his chest", "against her",
    ],
    "vulnerability_care": [
        "wounded", "injured", "bleeding", "bandage", "fever", "unconscious",
        "don't die", "i'm scared", "protect you", "safe with me", "hurts",
        "bloodied", "collapsed", "soaked in blood", "gravely", "wound",
        "stitches", "tended to", "cradled", "cradling",
    ],
    "confession_secrecy": [
        "i never meant", "secret", "promise me", "between us", "don't tell anyone",
        "can you forgive", "i was wrong", "trust me", "i love you",
    ],
}

# Categories treated as high-impact for scoring
_HIGH_IMPACT = {
    "betrayal_disownment", "ultimatums_threats", "power_shifts_control",
    "strong_refusals", "vulnerability_care",
}


def _text_matches_taxonomy(text: str) -> float:
    """Return a trigger score based on the universal taxonomy."""
    text_l = text.lower()
    score = 0.0
    for category, phrases in TRIGGER_TAXONOMY.items():
        if any(p in text_l for p in phrases):
            if category in _HIGH_IMPACT:
                score = max(score, 0.85)
            elif category in ("romance_intimacy", "confession_secrecy", "emotional_breaks"):
                score = max(score, 0.72)
            else:
                score = max(score, 0.65)
    return score


_SHOT_MARKERS = (
    "medium shot", "close-up", "close up", "wide shot", "extreme close",
    "camera", "framing the", "macro shot", "tracking shot", "over-the-shoulder",
    "pov shot", "two-shot", "insert shot",
)


def _is_shot_description(text: str) -> bool:
    """True for pure camera-direction lines with no spoken dialogue."""
    t = (text or "").lower()
    if not t:
        return False
    has_dialogue_quote = ('"' in text) or ("“" in text) or ("«" in text)
    if has_dialogue_quote:
        return False
    return any(m in t for m in _SHOT_MARKERS)


def _beat_trigger_score(beat: Beat) -> float:
    """Composite promo-worthiness score for a single beat."""
    text = (beat.text or "").strip()
    if not text:
        return 0.0

    score = _text_matches_taxonomy(text)
    words = text.split()
    btype = (beat.type or "").upper()
    text_l = text.lower()

    # Punchy dialogue length — strongly preferred for promos
    if btype == "DIALOGUE" and 3 <= len(words) <= 30:
        score += 0.28
    elif btype == "DIALOGUE":
        score += 0.15
    elif 6 <= len(words) <= 40:
        score += 0.08

    if text.endswith("?") and len(text) > 10:
        score += 0.16
    if "!" in text or "..." in text:
        score += 0.10

    emotion = (beat.emotion or "").lower()
    if emotion in ("angry", "furious", "devastated", "shocked", "crying",
                   "heartbroken", "betrayed", "passionate", "afraid", "terrified"):
        score += 0.30
    elif emotion in ("tense", "determined", "cold", "sad", "tender", "soft", "worried"):
        score += 0.16
    elif emotion in ("intimate", "romantic", "vulnerable", "gentle"):
        score += 0.22

    # Action / physical stakes
    action_hits = [
        "blood", "wound", "collapse", "kiss", "embrace", "slap", "grab",
        "tear", "cry", "fall", "gun", "sword", "hit", "tremble", "stare",
        "bleeding", "cradled", "leaned",
    ]
    if any(h in text_l for h in action_hits):
        score += 0.32 if btype in ("ACTION", "CAMERA") else 0.18

    # Pure shot-direction lines are weak promo hooks unless they carry action stakes
    if _is_shot_description(text):
        if any(h in text_l for h in action_hits):
            score *= 0.85
        else:
            score *= 0.25

    intensity = getattr(beat, "intensity", None)
    if intensity is not None:
        try:
            iv = float(intensity)
            if iv > 1.0:
                iv = iv / 10.0
            score += max(0.0, min(0.4, iv * 0.4))
        except (TypeError, ValueError):
            pass

    return score


def find_trigger_beats(scene: Scene, mode: str = "rule", min_intensity: float = 0.28) -> List[int]:
    """
    Find beats that feel like strong emotional/dialogue triggers.

    Modes:
        rule   - Pure keyword taxonomy + secondary signals (fast, deterministic)
        hybrid - Keyword taxonomy first, then LLM semantic fallback on borderline beats
        llm    - LLM directly extracts the most promo-worthy trigger beats

    Always applies a coverage floor: if a scene has dialogue but <2 triggers,
    keep the top-scoring beats so soft-drama episodes are not left empty.
    """
    if mode == "llm":
        llm_hits = _find_trigger_beats_llm(scene)
        if llm_hits:
            return llm_hits
        mode = "rule"

    beats = scene.beats or []
    scored: List[tuple] = []  # (score, idx)

    for i, beat in enumerate(beats):
        s = _beat_trigger_score(beat)
        if s > 0:
            scored.append((s, i))

    triggers = sorted(i for s, i in scored if s >= min_intensity)

    # Coverage floor: ensure at least a few candidates per scene with content
    if len(triggers) < 2 and scored:
        scored_sorted = sorted(scored, key=lambda x: x[0], reverse=True)
        # Take top 3 (or fewer) above a soft floor
        floor = [i for s, i in scored_sorted if s >= 0.12][:6]
        triggers = sorted(set(triggers + floor))

    # Hybrid: if still sparse, ask LLM
    if mode == "hybrid" and len(triggers) < 2:
        llm_triggers = _find_trigger_beats_llm_semantic_fallback(scene, triggers)
        triggers = sorted(set(triggers + llm_triggers))

    return triggers


def _find_trigger_beats_llm(scene: Scene) -> List[int]:
    """Pure LLM mode: ask the model to return the best trigger beat indices."""
    try:
        from groq import Groq
        import os
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return []
        client = Groq(api_key=api_key)

        # Build a compact representation of the scene
        beat_lines = []
        for idx, b in enumerate(scene.beats):
            t = (b.text or "")[:80].replace("\n", " ")
            beat_lines.append(f"[{idx}] {t}")
        scene_text = "\n".join(beat_lines)

        prompt = f"""You are a drama promo editor. Given the following scene beats, 
return ONLY a JSON array of the 2-4 most dramatically powerful beat indices that would make 
the best 20-60 second storytelling hook for a TV promo. Focus on betrayal, ultimatums, 
emotional explosions, secrets, power shifts, or major cliffhangers.

Scene beats:
{scene_text}

Respond with ONLY a JSON array like [3, 7, 12]. No explanation."""

        resp = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=80,
        )
        content = resp.choices[0].message.content.strip()
        # Very defensive parsing
        import json, re
        match = re.search(r'\[.*?\]', content)
        if match:
            indices = json.loads(match.group(0))
            # Validate indices
            return [i for i in indices if isinstance(i, int) and 0 <= i < len(scene.beats)]
        return []
    except Exception:
        return []


def _find_trigger_beats_llm_semantic_fallback(scene: Scene, existing: List[int]) -> List[int]:
    """Hybrid mode fallback: ask LLM to find additional semantically strong beats."""
    try:
        from groq import Groq
        import os
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return []
        client = Groq(api_key=api_key)

        beat_lines = []
        for idx, b in enumerate(scene.beats):
            if idx in existing:
                continue
            t = (b.text or "")[:70].replace("\n", " ")
            beat_lines.append(f"[{idx}] {t}")
        if not beat_lines:
            return []

        scene_text = "\n".join(beat_lines)
        prompt = f"""Given these remaining beats from a dramatic scene, return a JSON array 
of up to 2 additional beat indices that feel like strong emotional triggers or turning points 
(even if they don't contain obvious keywords). Only pick truly powerful moments.

Beats:
{scene_text}

Return ONLY a JSON array, e.g. [5, 9]."""

        resp = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=60,
        )
        content = resp.choices[0].message.content.strip()
        import json, re
        match = re.search(r'\[.*?\]', content)
        if match:
            indices = json.loads(match.group(0))
            return [i for i in indices if isinstance(i, int) and 0 <= i < len(scene.beats)]
        return []
    except Exception:
        return []


def expand_window(scene: Scene, start_idx: int, max_duration: int = 90) -> Optional[Dict]:
    """Expand from a trigger beat into a natural ~15-60s story window.

    Expands **forward and backward** so late-scene triggers still form a full arc.
    """
    beats = scene.beats
    if not beats or start_idx >= len(beats) or start_idx < 0:
        return None

    trigger = beats[start_idx]
    t_start = trigger.start_sec or 0.0
    t_end = trigger.end_sec or (t_start + 3.0)

    stop_phrases = [
        "disown", "get out", "never", "end", "over", "swear",
        "kiss", "don't die", "i love you", "stay with me", "promise me",
        "i'm sorry", "forgive me", "the truth",
    ]

    # --- Forward expansion (cliff / exit) ---
    end_idx = start_idx
    for i in range(start_idx + 1, len(beats)):
        b = beats[i]
        dur_from_trigger = (b.end_sec or 0) - t_start
        if dur_from_trigger > max_duration:
            break
        text = (b.text or "").lower()
        end_idx = i
        if any(p in text for p in stop_phrases) and dur_from_trigger >= 12:
            break

    # --- Backward expansion (setup / hook lead-in) ---
    win_start_idx = start_idx
    target_min = 18.0
    target_ideal = 35.0
    for i in range(start_idx - 1, -1, -1):
        b = beats[i]
        # provisional duration if we take this earlier start
        prov_end = beats[end_idx].end_sec or t_end
        prov_start = b.start_sec or 0.0
        prov_dur = prov_end - prov_start
        if prov_dur > max_duration:
            break
        win_start_idx = i
        if prov_dur >= target_ideal:
            break

    win_start_beat = beats[win_start_idx]
    win_end_beat = beats[end_idx]
    start_sec = win_start_beat.start_sec or 0.0
    end_sec = win_end_beat.end_sec or (start_sec + 30)
    duration = end_sec - start_sec

    # Trim if still too long: keep a ~50s slice ending on the window end
    if duration > 65:
        target_start = end_sec - 50
        for i in range(win_start_idx, end_idx + 1):
            if (beats[i].start_sec or 0) >= target_start:
                win_start_idx = i
                break
        start_sec = beats[win_start_idx].start_sec or target_start
        duration = end_sec - start_sec

    # If still too short, push end forward more aggressively
    if duration < 12:
        for i in range(end_idx + 1, len(beats)):
            end_idx = i
            end_sec = beats[i].end_sec or end_sec
            duration = end_sec - start_sec
            if duration >= target_min:
                break
        # Or push start earlier
        if duration < 12:
            for i in range(win_start_idx - 1, -1, -1):
                win_start_idx = i
                start_sec = beats[i].start_sec or start_sec
                duration = end_sec - start_sec
                if duration >= target_min:
                    break

    if duration < 8:
        return None

    # Full dialogue/text across the window (needed for mini-arc + scoring)
    window_texts = []
    for i in range(win_start_idx, end_idx + 1):
        t = (beats[i].text or "").strip()
        if t:
            window_texts.append(t)
    full_text = " ".join(window_texts)

    trigger_text = (trigger.text or "")[:120]
    # Prefer a spoken / quoted line as the poster quote when trigger is camera direction
    if _is_shot_description(trigger_text) or (trigger.type or "").upper() in ("CAMERA", "ACTION"):
        best_quote = None
        for i in range(win_start_idx, end_idx + 1):
            bt = beats[i]
            t = (bt.text or "").strip()
            if not t:
                continue
            if (bt.type or "").upper() == "DIALOGUE":
                best_quote = t
                break
            if any(q in t for q in ('"', "“", "«")) and not best_quote:
                best_quote = t
        if best_quote:
            trigger_text = best_quote[:120]

    return {
        "start_idx": win_start_idx,
        "end_idx": end_idx,
        "start_sec": start_sec,
        "end_sec": end_sec,
        "duration_sec": round(duration, 1),
        "trigger_text": trigger_text,
        "window_text": full_text[:2000],
    }


def _windows_overlap(a: StoryPromoCandidate, b: StoryPromoCandidate, iou_thresh: float = 0.55) -> bool:
    """True if two candidates on the same episode heavily overlap in time."""
    if a.episode != b.episode:
        return False
    start = max(a.start_sec, b.start_sec)
    end = min(a.end_sec, b.end_sec)
    if end <= start:
        return False
    inter = end - start
    union = max(a.end_sec, b.end_sec) - min(a.start_sec, b.start_sec)
    if union <= 0:
        return False
    return (inter / union) >= iou_thresh


def _dedupe_candidates(cands: List[StoryPromoCandidate]) -> List[StoryPromoCandidate]:
    """Drop near-duplicate windows; keep the longer arc when overlapping."""
    kept: List[StoryPromoCandidate] = []
    ordered = sorted(cands, key=lambda c: (c.episode, -(c.duration_sec or 0), c.start_sec))
    for c in ordered:
        if any(_windows_overlap(c, k) for k in kept):
            continue
        kept.append(c)
    kept.sort(key=lambda c: (c.episode, c.start_sec))
    return kept


def generate_story_windows(episodes: List[Episode], mode: str = "rule") -> List[StoryPromoCandidate]:
    """Main Step 2: Generate storytelling promo candidates from episodes.

    mode: "rule" | "hybrid" | "llm" — controls trigger detection strategy.
    """
    def _maybe_add(ep_num, scene, t_idx, window, bag: List[StoryPromoCandidate]) -> None:
        if not window:
            return
        wtext = window.get("window_text") or window["trigger_text"] or ""
        if not wtext.strip():
            return
        if _is_shot_description(wtext) and _text_matches_taxonomy(wtext) < 0.5:
            if '"' not in wtext and "“" not in wtext and not any(
                h in wtext.lower()
                for h in ("blood", "kiss", "wound", "love", "die", "never", "father", "mother")
            ):
                return
        bag.append(
            StoryPromoCandidate(
                episode=ep_num,
                scene_ids=[scene.id],
                start_sec=window["start_sec"],
                end_sec=window["end_sec"],
                duration_sec=window["duration_sec"],
                trigger_beat_index=t_idx,
                trigger_text=window["trigger_text"],
                window_text=wtext,
            )
        )

    candidates: List[StoryPromoCandidate] = []

    for ep in episodes:
        for scene in ep.scenes:
            trigger_indices = find_trigger_beats(scene, mode=mode)
            for t_idx in trigger_indices:
                # Primary natural window
                _maybe_add(ep.number, scene, t_idx, expand_window(scene, t_idx, max_duration=90), candidates)
                # Secondary tighter punch window (helps fill top-k with variety)
                tight = expand_window(scene, t_idx, max_duration=40)
                if tight and (tight.get("duration_sec") or 0) >= 12:
                    # Only keep if meaningfully shorter than a long sibling would be
                    if (tight.get("duration_sec") or 0) <= 36:
                        _maybe_add(ep.number, scene, t_idx, tight, candidates)

    return _dedupe_candidates(candidates)


def generate_candidates(episodes: List[Episode], mode: str = "rule") -> List[StoryPromoCandidate]:
    """Public entry point used by the orchestrator."""
    return generate_story_windows(episodes, mode=mode)


if __name__ == "__main__":
    eps = load_episodes("data/processed")
    cands = generate_story_windows(eps, mode="rule")
    print(f"Generated {len(cands)} story windows")
    for c in cands[:5]:
        print(f"  Ep {c.episode}: {c.duration_sec}s - {c.trigger_text[:60]}...")