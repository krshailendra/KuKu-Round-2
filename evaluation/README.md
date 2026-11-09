# Evaluation Harness

## Purpose
This is a **lightweight but meaningful** evaluation system for the promo detection pipeline.

It sits between "just looking at JSON" and "heavy academic evaluation".

**It is general-purpose** — works with any episodes, not tied to specific ones.

## Structure
- `gold_labels.json` — Manually labeled good/ok/bad moments (add labels for any episode)
- `evaluator.py` — Computes Precision@K and basic diagnostics
- `results/` — Store before/after runs for comparison

## How to Use

### 1. Run Evaluation
```bash
python evaluation/evaluator.py --report data/processed/promo_report_ep4-5.json --k 5
```

You can point it at **any** promo report:
```bash
python evaluation/evaluator.py --report data/processed/promo_report_per_episode.json --k 5
```

### 2. Adding New Labels
Open `gold_labels.json` and add new entries under `"labels"`:
```json
{
  "episode": "012",
  "timestamp": "00:45.00 - 00:48.00",
  "text": "...",
  "label": "good",
  "notes": "..."
}
```

### 3. After Making Improvements
Re-run the pipeline, then run the evaluator again and compare:
- Precision@5 (Good only)
- Precision@5 (Good + Okay)
- Distribution of good/ok/bad in top results

## Label Definitions
- **good**: Strong promo moment — clear luxury signal + respects immersion
- **okay**: Acceptable but not great (some potential, weak luxury signal, or minor immersion risk)
- **bad**: Should not be recommended (breaks immersion, wrong emotional tone, or no real product opportunity)

## Philosophy
- Keep the gold set small (15-30 examples) but high quality
- Focuses on Top-5 / Top-10 results (what actually matters in production)
- Make it easy to expand when we add new episodes or improvements
- Works across any number of episodes
