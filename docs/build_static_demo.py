"""Build a static always-on demo site (Vercel / GitHub Pages).

No FastAPI needed to *view* the full 50-ep hybrid pack.
Generate/upload stay on a separate backend if you add one later.

Usage:
  python docs/build_static_demo.py
  # → writes deploy/static_site/
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "deploy" / "static_site"
SEED = ROOT / "data" / "projects" / "e3226269c4" / "output"
STATIC = ROOT / "web" / "static"


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    from web.services import data_layer as dl

    dl.bootstrap()
    # Force-load seed results
    ok = dl.load_project_results("e3226269c4")
    if not ok:
        raise SystemExit("Failed to load seed project results — check FINAL_PROMOS_hybrid.json")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # Copy UI assets
    (OUT / "static").mkdir(parents=True)
    for sub in ("css", "js", "img"):
        src = STATIC / sub
        if src.is_dir():
            shutil.copytree(src, OUT / "static" / sub)

    # Patch index: static demo banner + flag
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    inject = """
  <script>window.__KUKU_STATIC_DEMO__ = true;</script>
  <style>
    .static-demo-banner{
      background:linear-gradient(90deg,#5b21b6,#7c3aed);
      color:#fff;text-align:center;padding:8px 12px;font-size:13px;
      font-family:system-ui,sans-serif;
    }
    .static-demo-banner a{color:#fde68a}
    body.static-demo [data-static-hide],
    body.static-demo .gen-panel,
    body.static-demo #btnGenerate,
    body.static-demo .upload-zone{display:none !important}
  </style>
"""
    if "</head>" in html:
        html = html.replace("</head>", inject + "\n</head>", 1)
    if "<body" in html:
        html = html.replace("<body", '<body class="static-demo"', 1)
        # banner after body open
        import re

        html = re.sub(
            r"(<body[^>]*>)",
            r'\1\n  <div class="static-demo-banner"><strong>Live demo — full hybrid pack (50 episodes)</strong> · precomputed results · always on · '
            r'upload/Generate disabled on this static host (scripts stay private)</div>',
            html,
            count=1,
        )
    # Fix asset paths if needed (already /static/...)
    (OUT / "index.html").write_text(html, encoding="utf-8")

    # Copy raw deliverables for download
    data_out = OUT / "data"
    data_out.mkdir(parents=True)
    for name in (
        "FINAL_PROMOS_hybrid.json",
        "FINAL_PROMOS_hybrid.md",
        "FINAL_PROMOS_hybrid_campaign_pack.csv",
        "FINAL_PROMOS_hybrid_posting_order.csv",
        "series_continuity_map.json",
        "promos_hybrid_top5.json",
        "FINAL_PROMOS.json",
    ):
        src = SEED / name
        if src.is_file():
            shutil.copy2(src, data_out / name)

    # API fixtures the existing frontend expects
    api = OUT / "api"
    snap = dl.snapshot()
    if not isinstance(snap, dict):
        snap = {}
    pack = dl.get_campaign_pack()
    posting = dl.get_posting_order()

    _write(
        api / "health.json",
        {
            "ok": True,
            "product": "KuKu Promo Finder",
            "version": "1.3.0-static",
            "static_demo": True,
            "demo_public": True,
            "groq_configured": False,
            "message": "Static host — full precomputed 50-ep hybrid pack",
        },
    )
    _write(
        api / "meta.json",
        {
            "modes": dl.mode_options(),
            "features": dl.feature_catalog(),
            "folders": [],
            "labels": dl.all_labels(),
            "projects": dl.list_projects(),
            "active_project_id": "e3226269c4",
            "active_id": "e3226269c4",
            "snapshot": snap,
            "static_demo": True,
            "default_mode": "hybrid",
        },
    )
    _write(api / "snapshot.json", snap)
    _write(
        api / "campaign.json",
        {
            "mode": snap.get("mode") or "hybrid",
            "pack": pack,
            "posting_order": posting,
        },
    )
    # Precompute common episode explorer responses
    for top_n in (2, 3, 5, 10):
        ep = dl.get_episode_promos(top_n=top_n, label=None, episode=None)
        _write(api / f"episodes_top{top_n}.json", ep)
    _write(api / "episodes.json", dl.get_episode_promos(top_n=5))
    _write(api / "labels.json", {"labels": dl.all_labels()})

    # Continuity payload (mirror app route)
    _write(
        api / "continuity.json",
        {
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
                    {"id": "hook", "label": "Hook power", "weight": 0.28},
                    {"id": "cliff", "label": "Cliffhanger pull", "weight": 0.22},
                    {"id": "emotion", "label": "Emotional charge", "weight": 0.14},
                    {"id": "clarity", "label": "Standalone clarity", "weight": 0.14},
                    {"id": "continuity", "label": "Series fit", "weight": 0.12},
                    {"id": "craft", "label": "Craft & duration", "weight": 0.10},
                ],
            },
        },
    )
    _write(api / "marketer.json", dl.marketer_payload())
    _write(api / "projects.json", {"projects": dl.list_projects(), "active_id": "e3226269c4"})

    # Static fetch shim — maps /api/* to fixtures without a backend
    shim = r"""
/* Static demo API shim — no server required */
(function () {
  if (!window.__KUKU_STATIC_DEMO__) return;
  var orig = window.fetch.bind(window);
  function j(path) {
    return orig(path).then(function (r) {
      if (!r.ok) throw new Error("static fixture missing: " + path);
      return r.json();
    });
  }
  window.fetch = function (input, init) {
    var url = typeof input === "string" ? input : (input && input.url) || "";
    var u = url.split("?")[0];
    var q = url.indexOf("?") >= 0 ? url.slice(url.indexOf("?") + 1) : "";
    var method = ((init && init.method) || "GET").toUpperCase();

    // Block mutating / generate paths politely
    if (method !== "GET" && method !== "HEAD") {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            ok: false,
            error:
              "This static demo is view-only (full 50-ep hybrid pack). Upload/Generate need a backend host.",
          }),
          { status: 501, headers: { "Content-Type": "application/json" } }
        )
      );
    }

    var map = {
      "/api/health": "/api/health.json",
      "/api/meta": "/api/meta.json",
      "/api/snapshot": "/api/snapshot.json",
      "/api/campaign": "/api/campaign.json",
      "/api/labels": "/api/labels.json",
      "/api/continuity": "/api/continuity.json",
      "/api/marketer": "/api/marketer.json",
      "/api/projects": "/api/projects.json",
    };
    if (map[u]) return orig(map[u], init);

    if (u === "/api/episodes") {
      var top = 5;
      var m = /(?:^|&)top_n=(\d+)/.exec(q);
      if (m) top = parseInt(m[1], 10) || 5;
      if ([2, 3, 5, 10].indexOf(top) >= 0) return orig("/api/episodes_top" + top + ".json", init);
      return orig("/api/episodes.json", init);
    }

    if (u.indexOf("/api/export") === 0) {
      // Point browsers at CSV downloads instead
      window.location.href = "/data/FINAL_PROMOS_hybrid_campaign_pack.csv";
      return Promise.resolve(new Response("", { status: 204 }));
    }

    return orig(input, init);
  };
})();
"""
    (OUT / "static" / "js" / "static_shim.js").write_text(shim.strip() + "\n", encoding="utf-8")

    # Insert shim before app.js
    html2 = (OUT / "index.html").read_text(encoding="utf-8")
    if "static_shim.js" not in html2:
        if 'src="/static/js/app.js"' in html2:
            html2 = html2.replace(
                'src="/static/js/app.js"',
                'src="/static/js/static_shim.js"></script>\n  <script src="/static/js/app.js"',
                1,
            )
        elif "static/js/app.js" in html2:
            html2 = html2.replace(
                "static/js/app.js",
                "static/js/static_shim.js\"></script>\n  <script src=\"static/js/app.js",
                1,
            )
        (OUT / "index.html").write_text(html2, encoding="utf-8")

    # Vercel config
    (OUT / "vercel.json").write_text(
        json.dumps(
            {
                "version": 2,
                "cleanUrls": True,
                "headers": [
                    {
                        "source": "/api/(.*)",
                        "headers": [{"key": "Cache-Control", "value": "public, max-age=300"}],
                    },
                    {
                        "source": "/data/(.*)",
                        "headers": [{"key": "Cache-Control", "value": "public, max-age=300"}],
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # README for the static folder
    (OUT / "README.md").write_text(
        "# KuKu static demo\n\nFull hybrid promo pack (50 episodes) — view only.\n\n"
        "Deploy this folder to **Vercel** or **GitHub Pages**.\n\n"
        "Rebuild: `python docs/build_static_demo.py`\n",
        encoding="utf-8",
    )

    n_pack = len(pack) if isinstance(pack, list) else 0
    pool = []
    if isinstance(snap, dict):
        # episode count from labels or pack
        pass
    print(f"Static site -> {OUT}")
    print(f"  campaign pack size: {n_pack}")
    print(f"  load_project_results: {ok}")
    print("Deploy: cd deploy/static_site && npx vercel --prod")
    print("   or: GitHub Pages from /deploy/static_site")


if __name__ == "__main__":
    main()
