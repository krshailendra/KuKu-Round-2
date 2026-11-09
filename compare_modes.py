"""Compare rule vs hybrid vs llm scoring modes on multiple episodes.

Usage:
    python compare_modes.py --episodes 5 10 15 20 25 30 35 --top-k 3
"""

import argparse
import time
from collections import defaultdict
from typing import Dict, List, Any

from src.orchestrator import run_targeted_pipeline


def _per_episode_counts(report: Dict[str, Any], episodes: List[int]) -> Dict[int, Dict[str, int]]:
    """Build per-episode raw/validated/final counts from a pipeline report."""
    counts = {ep: {"raw": 0, "validated": 0, "final": 0} for ep in episodes}

    # Prefer explicit per_episode breakdown if present
    per_ep = report.get("per_episode") or {}
    if per_ep:
        for ep_str, stats in per_ep.items():
            try:
                ep = int(ep_str)
            except (TypeError, ValueError):
                continue
            if ep in counts:
                counts[ep]["raw"] = int(stats.get("raw", 0) or 0)
                counts[ep]["validated"] = int(stats.get("validated", 0) or 0)
                counts[ep]["final"] = int(stats.get("final", 0) or 0)
        return counts

    # Fallback: derive from final_promos + totals (raw is only global)
    finals = report.get("final_promos") or []
    for p in finals:
        ep = p.get("episode") if isinstance(p, dict) else getattr(p, "episode", None)
        if ep in counts:
            counts[ep]["final"] += 1

    # If only global totals exist, attach them to the first episode for visibility
    total_raw = int(report.get("total_candidates", 0) or 0)
    total_val = int(report.get("validated", report.get("validated_count", 0)) or 0)
    if episodes and total_raw and sum(c["raw"] for c in counts.values()) == 0:
        counts[episodes[0]]["raw"] = total_raw
        counts[episodes[0]]["validated"] = total_val

    return counts


def run_mode(episodes: List[int], mode: str, top_k: int) -> Dict[str, Any]:
    print(f"\n{'='*60}")
    print(f"RUNNING MODE: {mode.upper()}")
    print(f"{'='*60}")
    t0 = time.time()
    results = run_targeted_pipeline(
        episode_numbers=episodes,
        top_k=top_k,
        scoring_mode=mode,
        mini_arc_mode="hybrid",
    )
    elapsed = time.time() - t0
    print(f"Mode {mode} finished in {elapsed:.1f}s")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", nargs="+", type=int, required=True)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    modes = ["rule", "hybrid", "llm"]
    all_results: Dict[str, Dict[str, Any]] = {}

    for mode in modes:
        try:
            all_results[mode] = run_mode(args.episodes, mode, args.top_k)
        except Exception as e:
            print(f"ERROR in mode {mode}: {e}")
            import traceback
            traceback.print_exc()
            all_results[mode] = {
                "total_candidates": 0,
                "validated": 0,
                "final_promos": [],
                "error": str(e),
            }

    # ---- Summary table ----
    print("\n" + "=" * 90)
    print("COMPARISON SUMMARY")
    print("=" * 90)
    header = (
        f"{'Episode':<10}"
        f"{'Rule Raw':>12}{'Hybrid Raw':>12}{'LLM Raw':>10}"
        f"{'Rule Final':>12}{'Hybrid Final':>14}{'LLM Final':>12}"
    )
    print(header)
    print("-" * 90)

    per_mode_counts = {
        mode: _per_episode_counts(all_results.get(mode, {}), args.episodes)
        for mode in modes
    }

    for ep in args.episodes:
        row = f"{ep:<10}"
        for mode in modes:
            raw = per_mode_counts[mode][ep]["raw"]
            row += f"{raw if raw else 0:>12}"
        for mode in modes:
            final = per_mode_counts[mode][ep]["final"]
            row += f"{final:>12}" if mode != "hybrid" else f"{final:>14}"
        print(row)

    print("\n--- GLOBAL TOTALS ---")
    for mode in modes:
        r = all_results.get(mode, {})
        raw = r.get("total_candidates", 0)
        val = r.get("validated", r.get("validated_count", 0))
        final = len(r.get("final_promos") or r.get("selected_promos") or [])
        err = r.get("error")
        line = f"{mode.upper():<8} raw={raw:<5} validated={val:<5} final={final:<5}"
        if err:
            line += f"  ERROR: {err}"
        print(line)

    # Sample finals
    print("\n--- SAMPLE FINAL PROMOS (first 3 per mode) ---")
    for mode in modes:
        finals = all_results.get(mode, {}).get("final_promos") or []
        print(f"\n[{mode.upper()}] {len(finals)} finals")
        for i, p in enumerate(finals[:3]):
            if isinstance(p, dict):
                ep = p.get("episode")
                dur = p.get("duration_sec")
                score = p.get("overall_score")
                text = (p.get("trigger_text") or "")[:70]
            else:
                ep = getattr(p, "episode", None)
                dur = getattr(p, "duration_sec", None)
                score = getattr(p, "overall_score", None)
                text = (getattr(p, "trigger_text", None) or "")[:70]
            print(f"  {i+1}. ep={ep} dur={dur}s score={score} | {text}")


if __name__ == "__main__":
    main()
