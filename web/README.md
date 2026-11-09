# KuKu Promo Finder — Product Prototype

Web UI for the assignment pipeline. Design cues from [kuku.app](https://kuku.app/): dark entertainment canvas, violet brand, gold priority accents.

## Run

```bash
pip install -r requirements-web.txt
python run_prototype.py
```

Open **http://127.0.0.1:8787**

## What you can do

| Area | Capability |
|------|------------|
| **Generate** | Script folder path / discovered packs / multi `.txt` upload |
| **Modes** | Rule (fast/offline) · **Hybrid (Recommended)** · LLM (taste) |
| **Campaign priority** | Excel-style table · ranks · labels · ordered segment times · hook/cliff/why |
| **Export Excel** | Assignment format + classification labels |
| **Episode explorer** | Top 2 / 3 / 5 per episode · filter by label (e.g. thrilling) |
| **Continuity & rank** | Series Continuity Map · ranking method transparency |
| **Marketer QA** | Protected heroes · cut list with reasons |
| **Features** | Full live feature catalog |

Pre-loads existing `output/final/FINAL_PROMOS_hybrid.json` so the UI is demoable immediately.
