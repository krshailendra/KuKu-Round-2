"""KuKu Promo Finder — product prototype API + UI."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.services import data_layer as dl

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="KuKu Promo Finder",
    description="Product prototype — find, rank, and export microdrama promos",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_static(request, call_next):
    response = await call_next(request)
    path = request.url.path or ""
    if path.startswith("/static/") or path == "/" or path.endswith(".html"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


@app.on_event("startup")
def _startup():
    # Writable runtime dirs on free hosts (HF / Render / Railway)
    for rel in ("data/projects", "data/uploads", "data/processed", "output"):
        try:
            (ROOT / rel).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    try:
        dl.bootstrap()
    except Exception as e:
        print(f"[web] bootstrap warning: {e}")
    print(
        "[web] demo_public=%s max_eps=%s groq=%s"
        % (
            os.getenv("DEMO_PUBLIC", ""),
            os.getenv("DEMO_MAX_EPISODES", "0"),
            "yes" if os.getenv("GROQ_API_KEY") else "no",
        )
    )


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "product": "KuKu Promo Finder",
        "version": "1.3.0",
        "demo_public": os.getenv("DEMO_PUBLIC", "").strip().lower() in ("1", "true", "yes"),
        "demo_max_episodes": int(os.getenv("DEMO_MAX_EPISODES", "0") or "0"),
        "default_mode": os.getenv("DEMO_DEFAULT_MODE", "hybrid"),
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
    }


@app.get("/api/meta")
def meta():
    try:
        return {
            "demo_public": os.getenv("DEMO_PUBLIC", "").strip().lower() in ("1", "true", "yes"),
            "demo_max_episodes": int(os.getenv("DEMO_MAX_EPISODES", "0") or "0"),
            "default_mode": os.getenv("DEMO_DEFAULT_MODE", "hybrid"),

            "modes": dl.mode_options(),
            "features": dl.feature_catalog(),
            "folders": dl.list_script_folders(),
            "labels": dl.all_labels(),
            "snapshot": dl.snapshot(),
            "projects": dl.list_projects(),
            "active_project_id": dl.get_active_project_id(),
        }
    except Exception as e:
        raise HTTPException(500, f"meta failed: {e}") from e


@app.get("/api/projects")
def projects_list():
    return {
        "projects": dl.list_projects(),
        "active_id": dl.get_active_project_id(),
    }


@app.post("/api/projects")
def projects_create(
    name: str = Form(...),
    description: str = Form(""),
):
    try:
        meta = dl.create_project(name=name, description=description)
        return {"ok": True, "project": meta}
    except Exception as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/projects/activate")
def projects_activate(project_id: str = Form(...)):
    try:
        return dl.set_active_project(project_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.delete("/api/projects/{project_id}")
def projects_delete(project_id: str):
    try:
        return dl.delete_project(project_id)
    except PermissionError as e:
        raise HTTPException(403, str(e)) from e
    except Exception as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/projects/{project_id}/upload")
async def projects_upload(
    project_id: str,
    files: list[UploadFile] = File(...),
):
    try:
        if not files:
            raise HTTPException(400, "Select a folder of .txt episode scripts")
        result = dl.save_project_scripts(project_id, files)
        return {"ok": True, **result}
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"upload failed: {e}") from e


@app.post("/api/projects/{project_id}/run")
def projects_run(
    project_id: str,
    mode: str = Form(None),
    top_k: int = Form(5),
    top_n: int = Form(25),
    use_marketer: str = Form("1"),
):
    try:
        mode = (mode or os.getenv("DEMO_DEFAULT_MODE", "hybrid") or "hybrid").strip().lower()
        job_id = dl.start_project_pipeline(
            project_id=project_id,
            mode=mode,
            top_k=top_k,
            top_n=top_n,
            use_marketer=use_marketer not in ("0", "false", "False", ""),
        )
        return {"ok": True, "job_id": job_id}
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"run failed: {e}") from e


@app.get("/api/snapshot")
def snapshot():
    return dl.snapshot()


@app.post("/api/load_mode")
def load_mode(mode: str = Form("hybrid")):
    """Optional: load a previously saved FINAL pack for demo/review."""
    try:
        return dl.load_mode(mode, force_enrich_pool=False)
    except Exception as e:
        raise HTTPException(500, f"load_mode failed: {e}") from e


@app.get("/api/campaign")
def campaign():
    try:
        snap = dl.snapshot()
        return {
            "mode": snap.get("mode"),
            "pack": dl.get_campaign_pack(),
            "posting_order": dl.get_posting_order(),
        }
    except Exception as e:
        raise HTTPException(500, f"campaign failed: {e}") from e


@app.get("/api/episodes")
def episodes(
    top_n: int = Query(5, ge=1, le=15),
    label: str | None = Query(None),
    episode: int | None = Query(None),
):
    try:
        return dl.get_episode_promos(top_n=top_n, label=label or None, episode=episode)
    except Exception as e:
        raise HTTPException(500, f"episodes failed: {e}") from e


@app.get("/api/labels")
def labels():
    return {"labels": dl.all_labels()}


@app.get("/api/continuity")
def continuity():
    snap = dl.snapshot()
    return {
        "continuity_map": snap.get("continuity_map") or dl.load_full_continuity_map(),
        "ranking_method": snap.get("ranking_method"),
        "campaign_meta": snap.get("campaign_meta"),
        "marketer": snap.get("marketer"),
        "label_counts": snap.get("label_counts"),
        "role_counts": snap.get("role_counts"),
        "explain": {
            "title": "How Continuity & Rank work",
            "steps": [
                "Map the series (characters, themes, arc)",
                "Score every promo with type-agnostic weights",
                "Build a diverse campaign pack",
                "Marketer QA protects heroes and cuts weak tail",
            ],
            "score_weights": [
                {"id": "hook", "label": "Hook power", "weight": 0.28, "why": "Cold-open punch a stranger feels in 2 seconds"},
                {"id": "cliff", "label": "Cliffhanger pull", "weight": 0.22, "why": "Makes the next watch inevitable"},
                {"id": "emotion", "label": "Emotional charge", "weight": 0.14, "why": "Stakes, heat, betrayal — felt not told"},
                {"id": "clarity", "label": "Standalone clarity", "weight": 0.14, "why": "Works without prior episodes"},
                {"id": "continuity", "label": "Series fit", "weight": 0.12, "why": "Touches spine themes / principals"},
                {"id": "craft", "label": "Craft & duration", "weight": 0.10, "why": "Clean segments, ad-length fit"},
            ],
        },
    }


@app.get("/api/marketer")
def marketer():
    return dl.marketer_payload()


@app.get("/api/export.xlsx")
def export_xlsx(
    which: str = Query("campaign", pattern="^(campaign|episode)$"),
    top_n: int = Query(3, ge=1, le=10),
    label: str | None = Query(None),
):
    try:
        buf = dl.build_excel_bytes(which=which, top_n=top_n, label=label or None)
    except Exception as e:
        raise HTTPException(500, f"export failed: {e}") from e
    fname = (
        f"kuku_promos_{which}"
        + (f"_top{top_n}" if which == "episode" else "")
        + (f"_{label}" if label else "")
        + ".xlsx"
    )
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.post("/api/scan_folder")
def scan_folder(
    folder: str = Form(...),
    parse: str = Form("false"),
):
    do_parse = str(parse).strip().lower() in ("1", "true", "yes", "on")
    try:
        return dl.scan_folder(folder.strip(), parse=do_parse)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Scan/parse failed: {e}") from e


@app.post("/api/generate")
def generate(
    mode: str = Form(None),
    folder: str = Form(""),
    top_k: int = Form(5),
    top_n: int = Form(25),
    use_marketer: str = Form("true"),
    episode_start: int = Form(1),
    episode_end: int = Form(50),
):
    try:
        mode = (mode or os.getenv("DEMO_DEFAULT_MODE", "hybrid") or "hybrid").strip().lower()
        if mode not in ("rule", "hybrid", "llm"):
            raise HTTPException(400, "mode must be rule|hybrid|llm")
        folder = (folder or "").strip() or None
        mk = str(use_marketer).strip().lower() in ("1", "true", "yes", "on")
        job_id = dl.start_generate_job(
            mode=mode,
            folder=folder,
            top_k=top_k,
            top_n=top_n,
            use_marketer=mk,
            episode_start=episode_start,
            episode_end=episode_end,
        )
        return {"job_id": job_id}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Generate failed: {e}") from e


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = dl.get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job


@app.post("/api/upload_scripts")
async def upload_scripts(files: list[UploadFile] = File(...)):
    dest = dl.UPLOADS / f"pack_{uuid.uuid4().hex[:8]}"
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files:
        name = f.filename or "episode.txt"
        if not name.lower().endswith(".txt"):
            continue
        path = dest / Path(name).name
        data = await f.read()
        path.write_bytes(data)
        saved.append(path.name)
    if not saved:
        raise HTTPException(400, "No .txt files uploaded")
    return {"folder": str(dest), "files": saved, "count": len(saved)}


# Static last so /api and / win
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
