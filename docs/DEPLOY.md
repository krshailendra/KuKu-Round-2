# Deploy KuKu Promo Finder — **full usable app**

## What “usable” means

| Feature | Public deploy |
|---------|----------------|
| **Demo project** with **complete** hybrid outputs for the **50-ep** assignment pack | Yes (scripts not published) |
| Browse Priority / By episode / Continuity / exports | Yes |
| **New project** → upload other episode `.txt` folders | Yes |
| **Generate** (rule / hybrid / llm) on uploaded scripts | Yes |
| Raw 50 assignment scripts on the server/git | **No** (your rule) |

This is a **real FastAPI app**, not a static brochure.

---

## Cold starts (honest)

**No free host** runs a full Python API 24/7 with zero wake time.

| Host | Full app? | After idle |
|------|-----------|------------|
| **Render free** | Yes (Docker) | Sleeps ~15 min → first open **~30–60s**, then normal |
| **Hugging Face Spaces free** | Yes (Docker) | Same class of sleep/wake |
| **Railway / Fly** | Yes | Credits / limits; not forever-free always-on |
| Vercel / GitHub Pages | Static only | Instant, but **no Generate** |

**Recommendation:** **Render free** or **HF Spaces** for the real product.  
Optional: free **UptimeRobot** (or similar) ping `https://YOUR-URL/api/health` every 5 minutes — often keeps free web services warmer (not guaranteed forever).

If a reviewer hits a cold start once, the next clicks are fast and **Generate works**.

---

## A) Render (recommended full app)

1. Push this repo to GitHub: `https://github.com/krshailendra/KuKu-Round-2`
2. [render.com](https://render.com) → **New → Blueprint** (uses `render.yaml`) **or** Web Service → Docker
3. **Secret env**
   - `GROQ_API_KEY` = your key *(Hybrid polish; rule mode works without it)*
4. Already set in blueprint:
   - `DEMO_PUBLIC=1`
   - `DEMO_MAX_EPISODES=50` (full-season packs; raise/lower if the free host struggles)
   - `DEMO_DEFAULT_MODE=hybrid`
   - `DEMO_LOCK_SEED=1` (demo project can’t be deleted)
5. Deploy → open `*.onrender.com`

**Flow for visitors**

1. Land on site → **Kuku Sample Show (demo)** already has the **full 50-ep results**
2. Click **New project** → name it → **upload** their episode `.txt` files  
3. **Generate** → wait for job → Priority / By episode populate  

---

## B) Hugging Face Spaces (full app)

See **[docs/HF_SPACES.md](HF_SPACES.md)**.

- SDK: **Docker** (root `Dockerfile`, port **7860**)
- Secret: `GROQ_API_KEY`
- Same product behavior as Render

---

## C) Local (same UX)

```bash
pip install -r requirements.txt
cp .env.example .env   # GROQ_API_KEY=
# optional public-like caps:
# DEMO_PUBLIC=1
# DEMO_MAX_EPISODES=50
python run_prototype.py
```

---

## Scripts policy

| In git / image | Not in git / image |
|----------------|--------------------|
| `data/projects/e3226269c4/output/*` (full hybrid pack) | `I Married a Broken Soldier…/*.txt` |
| App code `src/`, `web/` | `data/projects/*/scripts/*.txt` |
| | `.env` / API keys |

Visitor uploads land only on the **host disk** (ephemeral on free tiers — fine for demos).

---

## After you re-run the assignment pipeline locally

```bash
# copy fresh outputs into the seed project
# then commit outputs (not scripts)
git add data/projects/e3226269c4/output
git commit -m "Refresh demo hybrid pack"
git push
# Render/HF redeploy → demo pack updates
```

---

## Optional static mirror

`python docs/build_static_demo.py` builds a **view-only** always-on copy (Vercel).  
Use only as a backup brochure — **not** the primary product you asked for.
