# KuKu Promo Finder (Round 2)

Find **shippable storytelling promo windows** from episode scripts, then rank a **campaign Priority pack** for the whole show.

**Product:** FastAPI + web UI · Hybrid default (rule core + optional Groq polish) · dual outputs (**By episode** + **Priority** pack).

---

## Live demo behavior (what we ship)

| On the public site | |
|--------------------|--|
| **Kuku Sample Show (demo)** | **Complete** hybrid results for the **full 50-episode** assignment (Priority, By episode, Continuity, CSVs) — **scripts not published** |
| **Someone else’s scripts** | **New project → upload `.txt` episodes → Generate** — fully works (public cap **50** eps/run — full season packs) |
| Assignment raw scripts | **Never** in git / Docker image |

This is a **full app**, not a static read-only page.

---

## Free hosting (full app)

| Host | Generate? | Cold start when idle? |
|------|-----------|------------------------|
| **Render free (Docker)** | Yes | Yes ~30–60s first open |
| **HF Spaces free (Docker)** | Yes | Yes ~30–60s first open |
| Vercel / GitHub Pages | View-only static | No sleep |

**There is no free always-on FastAPI.** For a **usable** product (upload + Generate), use **Render** or **HF Spaces**. After wake, the app is normal.

Guide: **[docs/DEPLOY.md](docs/DEPLOY.md)** · HF: **[docs/HF_SPACES.md](docs/HF_SPACES.md)**

Repo target: `https://github.com/krshailendra/KuKu-Round-2`

---

## Quick start (local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set GROQ_API_KEY (optional for rule-only)
python run_prototype.py
```

Open http://127.0.0.1:8787

---

## Deploy (Render — 5 minutes)

1. Push this repo to GitHub  
2. Render → New Web Service / Blueprint (`render.yaml`) → **Docker**  
3. Secret: `GROQ_API_KEY`  
4. Open the URL → demo pack already loaded → create project to try other scripts  

---

## Pipeline (short)

1. Parse scripts → scenes/beats  
2. Expand windows (~15–60s) — rule  
3. Mini-arc gate — rule in product  
4. Score + types — Hybrid polishes top-N/ep when Groq key present  
5. Top-K per episode → By episode  
6. Continuity map → series rank + diversity  
7. Marketer protect/reject → Priority pack  

Details: [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) · PDF under `docs/`.

---

## Env vars

| Var | Purpose |
|-----|---------|
| `GROQ_API_KEY` | Hybrid/LLM polish (rule works without it) |
| `DEMO_PUBLIC=1` | Public-demo guards |
| `DEMO_MAX_EPISODES` | Max `.txt` files per Generate (default **50** on deploy) |
| `DEMO_LOCK_SEED=1` | Seed demo project not deletable |
| `PORT` | Injected by host (7860 on HF, random on Render) |

---

## License / assignment

Built for the KuKu AI Generalist assignment — Find the Promos track. Public demo ships **derived promo cards**, not the raw episode script pack.
