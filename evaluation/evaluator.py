"""
Lightweight Evaluation Harness for Promo Detection.

Usage:
    python evaluation/evaluator.py --report data/processed/promo_report_ep4-5.json --k 5

This is an intermediate evaluation approach:
- Small gold label set (~12-15 examples)
- Computes Precision@K and basic diagnostics
- Easy to expand over time
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict


def load_gold_labels(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Create lookup: (episode, timestamp) -> label info
    lookup = {}
    for item in data["labels"]:
        key = (item["episode"], item["timestamp"])
        lookup[key] = item
    return lookup, data


def load_report(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_episode_key(ep_key: str) -> str:
    """Extract a clean episode identifier from various formats.
    Examples: 'episode_004' -> '004', 'ep_12' -> '012', 'episode_10' -> '010'
    """
    ep = ep_key.lower()
    ep = ep.replace("episode_", "").replace("ep_", "").replace("episode", "").replace("ep", "")
    ep = ep.strip("_- ").zfill(3)
    return ep


def evaluate(report_path: str, gold_path: str, k: int = 5):
    gold_lookup, gold_meta = load_gold_labels(gold_path)
    report = load_report(report_path)

    results = {
        "total_top_k": 0,
        "good_count": 0,
        "okay_count": 0,
        "bad_count": 0,
        "unlabeled_count": 0,
        "details": []
    }

    per_episode_stats = defaultdict(lambda: {"good": 0, "okay": 0, "bad": 0, "unlabeled": 0})

    for ep_key, candidates in report.items():
        ep_num = normalize_episode_key(ep_key)
        top_k = candidates[:k]

        for cand in top_k:
            results["total_top_k"] += 1
            ts = cand.get("timestamp", "")
            key = (ep_num, ts)

            if key in gold_lookup:
                label_info = gold_lookup[key]
                label = label_info["label"]
                results[f"{label}_count"] += 1
                per_episode_stats[ep_num][label] += 1
            else:
                results["unlabeled_count"] += 1
                per_episode_stats[ep_num]["unlabeled"] += 1

            results["details"].append({
                "episode": ep_num,
                "timestamp": ts,
                "text": cand.get("text", "")[:80],
                "score": cand.get("score", 0),
                "label": label_info["label"] if key in gold_lookup else "unlabeled",
                "notes": label_info.get("notes", "") if key in gold_lookup else ""
            })

    # Compute metrics
    precision_good = results["good_count"] / results["total_top_k"] if results["total_top_k"] > 0 else 0
    precision_good_okay = (results["good_count"] + results["okay_count"]) / results["total_top_k"] if results["total_top_k"] > 0 else 0

    print("\n" + "="*70)
    print("EVALUATION REPORT")
    print("="*70)
    print(f"Gold labels file : {gold_path}")
    print(f"Report file      : {report_path}")
    print(f"Top-K evaluated  : {k}")
    print("-"*70)
    print(f"Total candidates evaluated : {results['total_top_k']}")
    print(f"Good  : {results['good_count']} ({precision_good*100:.1f}%)")
    print(f"Okay  : {results['okay_count']}")
    print(f"Bad   : {results['bad_count']}")
    print(f"Unlabeled : {results['unlabeled_count']}")
    print("-"*70)
    print(f"Precision@ {k} (Good only)           : {precision_good:.3f}")
    print(f"Precision@ {k} (Good + Okay)         : {precision_good_okay:.3f}")
    print("="*70)

    # Per-episode breakdown
    print("\nPer-Episode Breakdown:")
    for ep, stats in sorted(per_episode_stats.items()):
        total = sum(stats.values())
        print(f"  Episode {ep}: Good={stats['good']}, Okay={stats['okay']}, Bad={stats['bad']}, Unlabeled={stats['unlabeled']} (Total={total})")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=str, default="data/processed/promo_report_ep4-5.json",
                        help="Path to promo report JSON")
    parser.add_argument("--gold", type=str, default="evaluation/gold_labels.json",
                        help="Path to gold labels JSON")
    parser.add_argument("--k", type=int, default=5, help="Top-K to evaluate")
    args = parser.parse_args()

    evaluate(args.report, args.gold, args.k)
