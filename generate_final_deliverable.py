"""Generate assignment final deliverable from hybrid (default) harvest.

Usage:
  python generate_final_deliverable.py
  python generate_final_deliverable.py --mode hybrid --top-n 25
  python generate_final_deliverable.py --top-n 0          # auto N in [20,30]
  python generate_final_deliverable.py --max-per-episode 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser(
        description="Build Series Continuity Map + global campaign pack + per-ep catalogue"
    )
    ap.add_argument("--mode", default="hybrid", choices=["rule", "hybrid", "llm"])
    ap.add_argument("--input", default=None, help="Path to promos_*_top5.json")
    ap.add_argument("--out-dir", default="output/final")
    ap.add_argument(
        "--top-n",
        type=int,
        default=0,
        help="Campaign pack size. 0 or omit = auto decide in [20,30]",
    )
    ap.add_argument(
        "--max-per-episode",
        type=int,
        default=2,
        help="Max promos from same episode in campaign pack",
    )
    ap.add_argument(
        "--no-marketer",
        action="store_true",
        help="Skip Marketer Agent trim (keep full scored pack)",
    )
    ap.add_argument(
        "--marketer-min",
        type=int,
        default=12,
        help="Marketer never leaves fewer than this many (except tiny pools)",
    )
    ap.add_argument(
        "--marketer-max",
        type=int,
        default=20,
        help="Marketer soft ceiling; strong hooks may mildly overflow",
    )
    ap.add_argument(
        "--marketer-llm",
        action="store_true",
        help="Optional LLM second opinion on borderline (not on protected)",
    )
    ap.add_argument(
        "--rerun-hybrid",
        action="store_true",
        help="Re-run hybrid pipeline 1-50 top_k=5 first",
    )
    ap.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args()

    if args.rerun_hybrid:
        from src.orchestrator import run_targeted_pipeline

        print("Re-running hybrid pipeline on eps 1-50...")
        report = run_targeted_pipeline(
            episode_numbers=list(range(1, 51)),
            top_k=args.top_k,
            mini_arc_mode="rule",
            scoring_mode="hybrid",
        )
        os.makedirs("output/full_compare", exist_ok=True)
        path = f"output/full_compare/promos_hybrid_top{args.top_k}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        args.input = path
        print(f"Saved {path}")

    inp = args.input or f"output/full_compare/promos_{args.mode}_top{args.top_k}.json"
    if not os.path.exists(inp):
        alt = f"output/full_compare/promos_{args.mode}_top5.json"
        if os.path.exists(alt):
            inp = alt
        else:
            print(f"Missing input: {inp}", file=sys.stderr)
            sys.exit(1)

    from src.final_deliverable import write_deliverable

    top_n = None if (args.top_n is None or args.top_n <= 0) else args.top_n

    result = write_deliverable(
        inp,
        out_dir=args.out_dir,
        mode_name=args.mode,
        episode_numbers=list(range(1, 51)),
        top_n=top_n,
        max_per_episode=args.max_per_episode,
        marketer_trim=not args.no_marketer,
        marketer_min_keep=args.marketer_min,
        marketer_max_keep=args.marketer_max,
        marketer_use_llm=args.marketer_llm,
    )
    doc = result["doc"]
    meta = doc.get("campaign_meta") or {}
    mk = meta.get("marketer") or {}
    print(f"Wrote {result['md']}")
    print(f"Wrote {result['json']}")
    if result.get("csv"):
        print(f"Wrote {result['csv']}")
    if result.get("continuity_map"):
        print(f"Continuity map: {result['continuity_map']}")
    print(f"Episodes with best promo: {doc['total_episodes_with_promo']}")
    print(f"Pool size: {doc.get('pool_size')}")
    print(
        f"Pre-marketer N={meta.get('top_n')} -> after marketer "
        f"N={meta.get('top_n_after_marketer')} "
        f"(cut={mk.get('cut_count')}, protected={mk.get('protected_count')}) "
        f"type_mix={meta.get('type_mix')}"
    )
    print(f"Missing: {doc.get('missing_episodes')}")
    if doc.get("marketer_cut_list"):
        print("\nMarketer cuts:")
        for c in doc["marketer_cut_list"][:20]:
            print(
                f"  - ep={c.get('episode')} old#{c.get('old_rank')} "
                f"g={c.get('series_global_score')} | {c.get('reason')} | "
                f"{(c.get('hook') or '')[:40]}"
            )
    print("\nCampaign pack (post first):")
    for r in (doc.get("campaign_pack") or [])[:20]:
        tc = r.get("timecode") or {}
        prot = "P" if r.get("marketer_protected") else " "
        print(
            f"  {prot}#{r.get('campaign_rank') or r.get('post_rank'):>2} "
            f"ep={r.get('episode'):>2} "
            f"global={r.get('series_global_score', r.get('series_score'))} "
            f"role={r.get('campaign_role')} "
            f"tags={r.get('promo_types')} "
            f"{tc.get('start_tc')}–{tc.get('end_tc')} | "
            f"{(r.get('hook') or '')[:50]}"
        )


if __name__ == "__main__":
    main()
