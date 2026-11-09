"""Main Pipeline Orchestrator - Storytelling Promo Generator.

Updated Pipeline:
1. Beat Parsing
2. Story Window Expansion (20-60s hook → cliffhanger)
3. Mini-Arc Validation (rule / llm / hybrid)
4. LLM Scoring (Hook, Cliffhanger, Emotion, Narrative, Pacing, Dialogue, Stakes)
5. Final Selection
6. Promo Type Classification
"""
import os
import json
import time
import asyncio
from collections import defaultdict
from typing import List, Dict, Tuple

from src.parser import parse_all
from src.candidate_generator import generate_story_windows, load_episodes
from src.llm_agents import run_agents_on_candidates, run_scoring_and_classification
from src.mini_arc_validator import validate_candidates
from src.promo_schemas import StoryPromoCandidate, PromoCandidate, PromoReport, save_json, MiniArcMode

# Episode beat storage for context-aware LLM analysis
_episodes_data: Dict[int, List[Dict]] = {}
_logline_map: Dict[int, str] = {}


def group_by_episode(candidates: List[PromoCandidate]) -> Dict[int, List[PromoCandidate]]:
    grouped = defaultdict(list)
    for c in candidates:
        grouped[c.episode].append(c)
    return grouped


def _norm_score(val) -> float:
    """Map 0-1 or 0-10 metrics onto 0-10 for ranking/filters."""
    if val is None:
        return 0.0
    try:
        v = float(val)
    except (TypeError, ValueError):
        return 0.0
    if 0 < v <= 1.5:
        v *= 10.0
    return max(0.0, min(10.0, v))


def rank_and_select(
    grouped: Dict[int, List],
    top_k: int = 5,
    hook_cliff_min: float = 3.5,
    min_gap_sec: float = 4.0,
) -> Dict[int, List]:
    """
    Hard filter + diversity-aware top-K selection.

    - Scores expected on 0-10 (0-1 values are auto-scaled).
    - hook_cliff_min is on 0-10 (default 3.5).
    - min_gap_sec prefers temporally spread promos within an episode.
    """
    result = {}
    for ep, cands in grouped.items():
        strong_cands = []
        for c in cands:
            h = _norm_score(getattr(c, "hook_strength", None))
            cl = _norm_score(getattr(c, "cliffhanger_strength", None))
            # Keep normalized fields on the object for reports
            if getattr(c, "hook_strength", None) is not None:
                try:
                    if float(c.hook_strength) <= 1.5:
                        c.hook_strength = h
                except (TypeError, ValueError):
                    pass
            if getattr(c, "cliffhanger_strength", None) is not None:
                try:
                    if float(c.cliffhanger_strength) <= 1.5:
                        c.cliffhanger_strength = cl
                except (TypeError, ValueError):
                    pass
            if getattr(c, "overall_score", None) is not None:
                os_ = _norm_score(c.overall_score)
                if os_ and float(c.overall_score or 0) <= 1.5:
                    c.overall_score = os_

            if h >= hook_cliff_min and cl >= hook_cliff_min:
                strong_cands.append(c)

        if not strong_cands:
            strong_cands = list(cands)

        def _score(x):
            return _norm_score(
                getattr(x, "overall_score", None)
                or getattr(x, "rank_score", None)
                or getattr(x, "final_score", None)
                or 0
            )

        sorted_cands = sorted(
            strong_cands,
            key=lambda x: (_score(x), getattr(x, "start_sec", 0) or 0),
            reverse=True,
        )

        # Diversity pass: prefer temporally spread promos
        selected = []
        for c in sorted_cands:
            if len(selected) >= top_k:
                break
            c_start = getattr(c, "start_sec", 0) or 0
            c_end = getattr(c, "end_sec", c_start) or c_start
            too_close = False
            for s in selected:
                s_start = getattr(s, "start_sec", 0) or 0
                s_end = getattr(s, "end_sec", s_start) or s_start
                if c_end < s_start:
                    gap = s_start - c_end
                elif s_end < c_start:
                    gap = c_start - s_end
                else:
                    gap = 0.0  # overlap
                if gap < min_gap_sec:
                    too_close = True
                    break
            if not too_close:
                selected.append(c)

        # Fill remaining slots without diversity so top_k is respected when possible
        if len(selected) < top_k:
            for c in sorted_cands:
                if c in selected:
                    continue
                selected.append(c)
                if len(selected) >= top_k:
                    break

        result[ep] = selected
    return result


def build_per_episode_report(top_per_ep: Dict[int, List[PromoCandidate]]) -> Dict:
    report = {}
    for ep in sorted(top_per_ep.keys()):
        promos = []
        for c in top_per_ep[ep]:
            promos.append({
                "timestamp": f"{c.beat_start} - {c.beat_end}",
                "scene": c.scene_id,
                "character": c.character,
                "text": c.text[:180] + ("..." if len(c.text) > 180 else ""),
                "reason": c.llm_reason,
                "score": c.final_score
            })
        report[f"episode_{ep:03d}"] = promos
    return report


def _build_episode_beat_data(episodes) -> Tuple[Dict[int, List[Dict]], Dict[int, str]]:
    """Flatten parsed episodes into beat lists + loglines for context-aware agents."""
    ep_data: Dict[int, List[Dict]] = {}
    loglines: Dict[int, str] = {}

    for ep in episodes:
        flat_beats = []
        for scene in ep.scenes:
            for beat in scene.beats:
                flat_beats.append({
                    "scene": scene.id,
                    "character": beat.character,
                    "text": beat.text,
                    "type": beat.type,
                })
        ep_data[ep.number] = flat_beats
        loglines[ep.number] = ep.logline or ""

    return ep_data, loglines


def run_full_pipeline():
    print("=== Step 1: Parsing episodes ===")
    episodes, ctx = parse_all()

    print("\n=== Step 2: Generating candidates ===")
    candidates = generate_candidates(episodes, mode=scoring_mode)
    print(f"Raw candidates found: {len(candidates)}")

    # Build episode beat data so agents can use context windows
    global _episodes_data, _logline_map
    _episodes_data, _logline_map = _build_episode_beat_data(episodes)

    print("\n=== Step 3: Running specialist agents (parallel + context windows) ===")
    enriched = run_agents_on_candidates(candidates, _logline_map, _episodes_data)
    print(f"Enriched {len(enriched)} candidates")

    print("\n=== Step 4: Ranking & per-episode output ===")
    grouped = group_by_episode(enriched)
    top_per_episode = rank_and_select(grouped, top_k=4)

    report = build_per_episode_report(top_per_episode)

    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/promo_report_per_episode.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n=== Done ===")
    print("Output written to: data/processed/promo_report_per_episode.json")
    print(f"Episodes with recommendations: {len(report)}")

    # Also save a simple summary
    summary = {
        "total_episodes": len(report),
        "total_recommended_promos": sum(len(v) for v in report.values())
    }
    with open("data/processed/pipeline_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def run_targeted_pipeline(
    episode_numbers: List[int],
    top_k: int = 3,
    mini_arc_mode: str = "hybrid",
    scoring_mode: str = "hybrid"
):
    """
    New Storytelling Promo Pipeline (2025-04)

    Steps:
    1. Parse episodes
    2. Story Window Expansion
    3. Mini-Arc Validation (rule / llm / hybrid)
    4. Scoring (rule / llm / hybrid)
    5. Final Selection
    6. Promo Type Classification
    """
    from src.parser import Episode
    from src.mini_arc_validator import validate_candidates
    from src.llm_agents import run_scoring_and_classification
    from src.promo_schemas import MiniArcMode

    total_start = time.time()
    print(f"=== Storytelling Promo Pipeline on episodes: {episode_numbers} ===")
    print(f"Mini-Arc Mode: {mini_arc_mode}")

    print("\n=== Step 1: Loading episodes ===")
    t0 = time.time()
    import glob as _glob
    from src.candidate_generator import load_episodes as _load_eps

    processed_files = _glob.glob("data/processed/ep_*.json")
    if len(processed_files) >= max(episode_numbers):
        print(f"  (reusing {len(processed_files)} processed JSON files)")
        all_episodes = _load_eps("data/processed")
    else:
        all_episodes, ctx = parse_all()
    print(f"  Load/parse took: {time.time() - t0:.1f}s")

    # Filter to requested episodes
    episodes = [ep for ep in all_episodes if ep.number in episode_numbers]
    if not episodes:
        print("No matching episodes found!")
        return {
            "episodes": episode_numbers,
            "total_candidates": 0,
            "validated": 0,
            "final_promos": [],
            "per_episode": {str(e): {"raw": 0, "validated": 0, "final": 0} for e in episode_numbers},
        }

    print(f"Loaded {len(episodes)} episodes")

    # Step 2: Story Window Expansion
    print("\n=== Step 2: Story Window Expansion ===")
    t0 = time.time()
    # Always rule-based expansion (taxonomy+coverage). scoring_mode is scoring-only.
    raw_candidates = generate_story_windows(episodes, mode="rule")
    print(f"  Window expansion took: {time.time() - t0:.1f}s")
    print(f"  Raw story windows: {len(raw_candidates)}")

    # Step 3: Mini-Arc Validation
    print(f"\n=== Step 3: Mini-Arc Validation ({mini_arc_mode}) ===")
    t0 = time.time()
    mode = MiniArcMode(mini_arc_mode)
    # llm_client=None → pure rule mini-arc (fast); hybrid still uses rule-first path
    validated = asyncio.run(validate_candidates(raw_candidates, episodes, mode=mode, llm_client=None))
    print(f"  Validation took: {time.time() - t0:.1f}s")
    print(f"  Valid mini-arcs: {len(validated)}")

    if not validated:
        print("No valid mini-arcs found. Falling back to raw_candidates for scoring.")
        validated = raw_candidates

    # Step 4 + 6: Scoring + Type Classification (rule / llm / hybrid)
    print(f"\n=== Step 4+6: Scoring + Promo Type Classification [{scoring_mode}] ===")
    t0 = time.time()

    client = None
    effective_mode = scoring_mode

    if scoring_mode in ("llm", "hybrid"):
        try:
            from groq import AsyncGroq
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except Exception:
                pass
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                client = AsyncGroq(api_key=groq_key)
            else:
                print("  (No GROQ_API_KEY found — falling back to rule mode)")
                effective_mode = "rule"
        except Exception as e:
            print(f"  (Groq client unavailable ({e}) — falling back to rule mode)")
            effective_mode = "rule"

    scored = asyncio.run(run_scoring_and_classification(validated, client, mode=effective_mode))
    print(f"  Scoring took: {time.time() - t0:.1f}s")

    # Step 5: Final Selection (diversity-aware top_k per episode)
    print("\n=== Step 5: Final Selection ===")
    from collections import defaultdict
    grouped: Dict[int, List] = defaultdict(list)
    for c in scored:
        grouped[c.episode].append(c)
    # Ensure every requested episode appears (even if empty)
    for ep_num in episode_numbers:
        grouped.setdefault(ep_num, [])

    ranked = rank_and_select(grouped, top_k=top_k)
    final_promos = []
    for ep_num in episode_numbers:
        final_promos.extend(ranked.get(ep_num, []))

    # Save report (with per-episode breakdown for compare_modes)
    def _ep_count(cands, ep):
        return sum(1 for c in cands if getattr(c, "episode", None) == ep)

    per_episode = {
        str(ep): {
            "raw": _ep_count(raw_candidates, ep),
            "validated": _ep_count(validated, ep),
            "final": _ep_count(final_promos, ep),
        }
        for ep in episode_numbers
    }

    os.makedirs("data/processed", exist_ok=True)
    out_path = f"data/processed/promo_report_ep{episode_numbers[0]}-{episode_numbers[-1]}.json"

    promo_dicts = [p.to_dict() for p in final_promos]
    report = {
        "episodes": episode_numbers,
        "mini_arc_mode": mini_arc_mode,
        "scoring_mode": scoring_mode,
        "total_candidates": len(raw_candidates),
        "validated": len(validated),
        "validated_count": len(validated),  # alias for older readers
        "final_promos": promo_dicts,
        "selected_promos": promo_dicts,  # alias for older readers
        "per_episode": per_episode,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    total_time = time.time() - total_start
    print(f"\n=== Done ===")
    print(f"Total pipeline time: {total_time:.1f}s")
    print(f"Output written to: {out_path}")
    print(f"Final promos selected: {len(final_promos)}")
    print(f"Per-episode: {per_episode}")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=50)
    args = parser.parse_args()
    run_full_pipeline(start=args.start, end=args.end)