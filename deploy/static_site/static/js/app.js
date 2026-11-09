/* KuKu Promo Finder — frontend (defensive, event-delegated) */
(function () {
  "use strict";

  var state = {
    mode: "hybrid",
    meta: null,
    campaign: [],
    projects: [],
    activeProjectId: null,
    activeProject: null,
  };

  function $(id) {
    return document.getElementById(id);
  }

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function tagClass(t) {
    var x = String(t || "").toLowerCase();
    if (x.indexOf("emotion") >= 0) return "emotional";
    if (x.indexOf("cliff") >= 0) return "cliffhanger";
    if (x.indexOf("roman") >= 0) return "romantic";
    if (x.indexOf("thrill") >= 0 || x.indexOf("tension") >= 0) return "thriller";
    if (x.indexOf("reveal") >= 0 || x.indexOf("twist") >= 0) return "revelation";
    return "";
  }

  function tagsHtml(list) {
    if (!list || !list.length) return '<span class="tag">untyped</span>';
    return list
      .map(function (t) {
        return '<span class="tag ' + tagClass(t) + '">' + escapeHtml(t) + "</span>";
      })
      .join("");
  }

  function segsHtml(segs) {
    if (!segs || !segs.length) return "—";
    return (
      '<div class="seg-chips">' +
      segs
        .map(function (s, i) {
          if (s == null) return "";
          if (typeof s === "string") {
            return '<span class="seg-chip">' + escapeHtml(s) + "</span>";
          }
          var start = s.start_tc || s.start || s.start_time || "";
          var end = s.end_tc || s.end || s.end_time || "";
          var role = s.role || s.label || s.beat_role || "beat";
          var idx = s.index != null ? s.index : i + 1;
          return (
            '<span class="seg-chip">' +
            escapeHtml(String(idx)) +
            ". " +
            escapeHtml(String(start)) +
            " → " +
            escapeHtml(String(end)) +
            " · " +
            escapeHtml(String(role)) +
            "</span>"
          );
        })
        .join("") +
      "</div>"
    );
  }

  function setText(id, text) {
    var el = $(id);
    if (el) el.textContent = text == null ? "" : String(text);
  }

  function setHtml(id, html) {
    var el = $(id);
    if (el) el.innerHTML = html == null ? "" : String(html);
  }

  function showProgress(msg, pct) {
    var wrap = $("progress-wrap");
    if (wrap) wrap.classList.add("show");
    setText("progress-msg", msg || "");
    var bar = $("progress-bar");
    if (bar && pct != null) bar.style.width = String(pct) + "%";
  }

  function api(path, opts) {
    opts = opts || {};
    return fetch(path, opts).then(function (res) {
      if (!res.ok) {
        return res
          .json()
          .catch(function () {
            return {};
          })
          .then(function (j) {
            throw new Error(j.detail || j.error || res.statusText || "Request failed");
          });
      }
      var ct = res.headers.get("content-type") || "";
      if (ct.indexOf("application/json") >= 0) return res.json();
      return res;
    });
  }

  function goto(view) {
    qsa(".view").forEach(function (v) {
      v.classList.remove("active");
    });
    qsa("#nav-tabs button, #nav button").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-view") === view);
    });
    var node = $("view-" + view);
    if (node) node.classList.add("active");

    if (view === "campaign") loadCampaign();
    else if (view === "episodes") loadEpisodes();
    else if (view === "continuity") renderContinuity();
    else if (view === "marketer") renderMarketer();
    else if (view === "features") renderFeaturesAll();
  }

  function renderModes(modes) {
    var root = $("mode-cards");
    if (!root) return;
    modes = modes || [];
    root.innerHTML = modes
      .map(function (m) {
        var selected = m.id === state.mode ? " selected" : "";
        var badge = m.badge ? '<span class="badge">' + escapeHtml(m.badge) + "</span>" : "";
        return (
          '<button type="button" class="mode-card' +
          selected +
          '" data-mode="' +
          escapeHtml(m.id) +
          '" data-action="pick-mode">' +
          '<div class="name">' +
          escapeHtml(m.label) +
          " " +
          badge +
          "</div>" +
          '<div class="blurb">' +
          escapeHtml(m.blurb || "") +
          "</div>" +
          '<div class="works"><strong>Works for:</strong> ' +
          escapeHtml(m.works_for || "") +
          "</div></button>"
        );
      })
      .join("");
  }

  function renderFeatures(list, targetId) {
    var root = $(targetId);
    if (!root) return;
    root.innerHTML = (list || [])
      .map(function (f) {
        return (
          '<div class="feature"><div class="top"><div class="name">' +
          escapeHtml(f.name) +
          '</div><span class="dot-live" title="live"></span></div>' +
          '<div class="desc">' +
          escapeHtml(f.desc || "") +
          "</div></div>"
        );
      })
      .join("");
  }

  function renderFeaturesAll() {
    if (state.meta && state.meta.features) renderFeatures(state.meta.features, "feature-grid-all");
    else if (state.meta && state.meta.snapshot)
      renderFeatures(state.meta.snapshot.features, "feature-grid-all");
  }

  function renderFolders(folders) {
    var root = $("folder-list");
    if (!root) return;
    if (!folders || !folders.length) {
      root.innerHTML =
        '<div class="empty" style="border:0;padding:12px">No script folders detected — paste a path or upload .txt files.</div>';
      return;
    }
    root.innerHTML = folders
      .map(function (f) {
        return (
          '<button type="button" class="folder-item" data-path="' +
          escapeHtml(f.path) +
          '"><div><div>' +
          escapeHtml(f.name) +
          '</div><div class="path">' +
          escapeHtml(f.path) +
          '</div></div><div class="pill">' +
          escapeHtml(String(f.script_count)) +
          " scripts</div></button>"
        );
      })
      .join("");
    var pathEl = $("folder-path");
    if (pathEl && !pathEl.value && folders[0]) pathEl.value = folders[0].path;
  }

  function renderSnapshot(snap) {
    if (!snap) return;
    state.mode = snap.mode || state.mode;
    setText("stat-campaign", snap.total_campaign != null ? String(snap.total_campaign) : "—");
    setText("stat-pool", snap.total_pool != null ? String(snap.total_pool) : "—");
    setText(
      "st-eps",
      snap.total_episodes_with_promo != null ? String(snap.total_episodes_with_promo) : "—"
    );
    setText(
      "st-cuts",
      snap.marketer && snap.marketer.cut_count != null ? String(snap.marketer.cut_count) : "—"
    );
    setText("mode-pill", "Mode: " + (snap.mode || "—"));
    setText(
      "loaded-meta",
      snap.source_path
        ? "Loaded " + (snap.mode || "") + " · " + (snap.loaded_at || "") + " · " + snap.source_path
        : "No deliverable loaded yet — generate or load a mode."
    );
    renderFeatures(snap.features, "feature-grid-home");
    renderFeatures(snap.features, "feature-grid-all");
  }

  function fillLabelSelect(labels) {
    ["ep-label", "camp-label"].forEach(function (id) {
      var sel = $(id);
      if (!sel) return;
      var cur = sel.value;
      sel.innerHTML =
        '<option value="">All labels</option>' +
        (labels || [])
          .map(function (l) {
            return (
              '<option value="' + escapeHtml(l) + '">' + escapeHtml(l) + "</option>"
            );
          })
          .join("");
      if (cur) sel.value = cur;
    });
  }

  function refreshMeta() {
    return api("/api/meta")
      .then(function (meta) {
        state.meta = meta;
        renderModes(meta.modes || []);
        if (meta.projects) {
          renderProjects(meta.projects || [], meta.active_project_id);
        }
        renderSnapshot(meta.snapshot);
        var labels = meta.labels || [];
        if (!labels.length && meta.snapshot && meta.snapshot.label_counts)
          labels = Object.keys(meta.snapshot.label_counts);
        fillLabelSelect(labels);
      })
      .catch(function (e) {
        setText("loaded-meta", "API error: " + (e.message || e));
      });
  }

  function loadCampaign() {
    var tb = qs("#camp-table tbody") || qs("#campaign-table tbody");
    if (!tb) {
      console.warn("[KuKu] camp-table missing in DOM");
      return;
    }
    tb.innerHTML =
      '<tr><td colspan="9"><div class="empty">Loading campaign pack…</div></td></tr>';
    api("/api/campaign")
      .then(function (data) {
        state.campaign = data.pack || data.posting_order || [];
        setText(
          "stat-campaign",
          state.campaign.length ? String(state.campaign.length) : "—"
        );
        paintCampaign();
      })
      .catch(function (e) {
        tb.innerHTML =
          '<tr><td colspan="9"><div class="empty">Failed: ' +
          escapeHtml(e.message || e) +
          "</div></td></tr>";
      });
  }

  function renderCampaign() {
    loadCampaign();
  }

  function paintCampaign() {
    var tb = qs("#camp-table tbody") || qs("#campaign-table tbody");
    if (!tb) return;
    var q = (($("camp-search") && $("camp-search").value) || "").toLowerCase().trim();
    var lab = ($("camp-label") && $("camp-label").value) || "";
    var rows = (state.campaign || []).filter(function (p) {
      if (lab) {
        var labels = p.promo_types || p.labels || [];
        if (labels.indexOf(lab) < 0) return false;
      }
      if (!q) return true;
      var blob = [
        p.hook,
        p.cliffhanger || p.cliff,
        p.why_it_works || p.why,
        p.campaign_role,
        String(p.episode || ""),
        (p.promo_types || []).join(" "),
      ]
        .join(" ")
        .toLowerCase();
      return blob.indexOf(q) >= 0;
    });
    if (!rows.length) {
      tb.innerHTML =
        '<tr><td colspan="9"><div class="empty">No promos in pack yet. Create a project → upload a script folder → Run full pipeline.</div></td></tr>';
      return;
    }
    tb.innerHTML = rows
      .map(function (p) {
        var rank = p.campaign_rank || p.post_rank || "—";
        var prot = p.marketer_protected
          ? '<span class="protect">PROTECTED</span>'
          : "";
        var score =
          p.series_global_score != null
            ? p.series_global_score
            : p.overall_score != null
              ? p.overall_score
              : "—";
        var segs = p.ordered_segments || p.segments || [];
        return (
          "<tr>" +
          '<td><div class="rank">#' +
          escapeHtml(String(rank)) +
          " " +
          prot +
          "</div></td>" +
          "<td>" +
          escapeHtml(String(p.episode != null ? p.episode : "")) +
          '</td><td class="mono">' +
          escapeHtml(String(score)) +
          '</td><td class="cell-text">' +
          escapeHtml(p.hook || "—") +
          '</td><td class="cell-text cliff">' +
          escapeHtml(p.cliffhanger || p.cliff || "—") +
          '</td><td class="cell-text why">' +
          escapeHtml(p.why_it_works || p.why || "—") +
          "</td><td>" +
          segsHtml(segs) +
          '</td><td><div class="tags">' +
          tagsHtml(p.promo_types || p.labels || []) +
          '</div></td><td><span class="tag role">' +
          escapeHtml(p.campaign_role || "—") +
          "</span></td></tr>"
        );
      })
      .join("");
  }

  function loadEpisodes() {
    var topN = ($("ep-topn") && $("ep-topn").value) || "5";
    var label = ($("ep-label") && $("ep-label").value) || "";
    var ep = ($("ep-num") && $("ep-num").value) || ($("ep-only") && $("ep-only").value) || "";
    var q = "top_n=" + encodeURIComponent(topN);
    if (label) q += "&label=" + encodeURIComponent(label);
    if (ep) q += "&episode=" + encodeURIComponent(ep);

    var root = $("ep-list");
    if (root) root.innerHTML = '<div class="empty">Loading…</div>';

    api("/api/episodes?" + q)
      .then(function (data) {
        var cloud = $("label-cloud");
        var counts = data.label_counts || {};
        if (cloud) {
          var keys = Object.keys(counts);
          cloud.innerHTML = keys
            .map(function (k) {
              return (
                '<button type="button" class="pill brand" data-lab="' +
                escapeHtml(k) +
                '">' +
                escapeHtml(k) +
                " · " +
                counts[k] +
                "</button>"
              );
            })
            .join("");
        }
        if (!root) return;
        if (!data.episodes || !data.episodes.length) {
          var te0 = (data && data.total_episodes) || 0;
          var pool0 = (data && data.pool_size) || 0;
          var activeHint = (data && (data.project_name || data.active_project || data.project_id)) || "";
          var msg;
          if (!te0 && !pool0) {
            msg =
              '<div class="empty">' +
              '<strong>No episodes loaded yet.</strong><br/>' +
              'Open <em>Projects</em>, select a show that already has results (FINAL_PROMOS), ' +
              'or run the pipeline / use <em>Load demo results</em>. ' +
              (activeHint ? ('Active: ' + escapeHtml(String(activeHint)) + '. ') : '') +
              'If a project just finished, refresh this page so bootstrap can pick it up.' +
              '</div>';
          } else {
            msg =
              '<div class="empty">No promos match this filter (0 shown' +
              (te0 ? '; ' + te0 + ' episode' + (te0 === 1 ? '' : 's') + ' in series' : '') +
              (pool0 ? '; ' + pool0 + ' promos in pool' : '') +
              '). Clear the label/episode filter or pick another project with results.</div>';
          }
          root.innerHTML = msg;
          return;
        }
        var shownN = data.episodes_shown != null ? data.episodes_shown : data.episodes.length;
        var totalEp = data.total_episodes != null ? data.total_episodes : shownN;
        var poolZ = data.pool_size != null ? data.pool_size : 0;
        var head =
          '<div class="muted" style="padding:4px 2px 10px">Showing ' +
          shownN +
          ' of ' +
          totalEp +
          ' episodes · ' +
          poolZ +
          ' promos in pool</div>';
        root.innerHTML =
          head +
          data.episodes
          .map(function (block) {
            var cards = (block.promos || [])
              .map(function (p, i) {
                var score =
                  p.series_global_score != null
                    ? p.series_global_score
                    : p.overall_score != null
                      ? p.overall_score
                      : "—";
                return (
                  '<article class="promo-card">' +
                  '<div class="meta"><span>#' +
                  (i + 1) +
                  " in ep · " +
                  escapeHtml(p.start_tc || "") +
                  " → " +
                  escapeHtml(p.end_tc || "") +
                  " · " +
                  escapeHtml(String(p.duration_sec != null ? p.duration_sec : "")) +
                  's</span><span class="score">' +
                  escapeHtml(String(score)) +
                  "</span></div>" +
                  '<div class="tags">' +
                  tagsHtml(p.promo_types) +
                  '<span class="chip tiny">' +
                  escapeHtml(String(p.pipeline_mode || state.mode || 'hybrid')) +
                  (p.score_source && String(p.score_source).toLowerCase() !== String(p.pipeline_mode || state.mode || 'hybrid').toLowerCase()
                    ? ' · ' + escapeHtml(String(p.score_source)) + ' check'
                    : '') +
                  '</span>' +
                  "</div>" +
                  '<div class="hook"><strong>Hook:</strong> ' +
                  escapeHtml(p.hook || "—") +
                  "</div>" +
                  '<div class="cliff"><strong>Cliffhanger:</strong> ' +
                  escapeHtml(p.cliffhanger || p.cliff || "—") +
                  "</div>" +
                  '<div class="why"><strong>Why it works:</strong> ' +
                  escapeHtml(p.why_it_works || "—") +
                  "</div>" +
                  '<div class="times">' +
                  segsHtml(p.ordered_segments || p.segments || []) +
                  "</div></article>"
                );
              })
              .join("");
            return (
              '<div class="ep-block"><div class="ep-head"><h3>Episode ' +
              escapeHtml(String(block.episode)) +
              '</h3><span class="pill">' +
              escapeHtml(String(block.count)) +
              " promo(s)</span></div>" +
              '<div class="promo-cards">' +
              cards +
              "</div></div>"
            );
          })
          .join("");
      })
      .catch(function (e) {
        if (root)
          root.innerHTML =
            '<div class="empty">Failed: ' + escapeHtml(e.message || e) + "</div>";
      });
  }

  function humanKey(k) {
    return String(k || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, function (c) {
        return c.toUpperCase();
      });
  }

  function explainCutReason(raw, fails) {
    var s = String(raw || "");
    var map = {
      "CUT:soft_short_hook":
        "Hook is too soft or short — a cold viewer won’t feel the punch in 2 seconds.",
      "CUT:relative_pack_size":
        "Trimmed to keep pack size usable — weaker than protected heroes already locked in.",
      "CUT:thin_hook": "Hook is generic / thin — doesn’t stand alone as an ad open.",
      "CUT:muddy_segments": "Segments are muddy or empty — hard to cut clean video.",
      "CUT:low_clarity": "Low standalone clarity — needs prior episodes to make sense.",
      "CUT:weak_tail": "Weak tail of the ranked list — not strong enough to post first.",
    };
    var base = map[s] || null;
    if (!base && s.indexOf("CUT:") === 0) {
      base = humanKey(s.replace(/^CUT:/, "")) + " — removed in Marketer QA.";
    }
    if (!base) base = s || "Removed in Marketer QA.";
    if (fails && fails.length) {
      base +=
        " Detail: " +
        fails
          .map(function (f) {
            return humanKey(String(f));
          })
          .join(", ") +
        ".";
    }
    return base;
  }

  function renderContinuity() {
    api("/api/continuity")
      .then(function (data) {
        var cm = data.continuity_map || {};
        var explain = data.explain || {};
        var oneLiner = cm.series_one_liner || cm.one_liner || "—";
        var epCount =
          cm.episodes_indexed ||
          cm.total_episodes ||
          cm.episode_count ||
          (cm.episodes && cm.episodes.length) ||
          "—";
        var rows = [
          ["Show map", cm.name || "Series Continuity Map"],
          ["Episodes indexed", String(epCount)],
          ["Series one-liner", oneLiner],
        ];
        if (cm._source_file) rows.push(["Loaded from", cm._source_file]);
        setHtml(
          "continuity-kv",
          rows
            .map(function (r) {
              return (
                '<div class="row"><b>' +
                escapeHtml(r[0]) +
                '</b><span style="text-align:left;max-width:70%">' +
                escapeHtml(String(r[1])) +
                "</span></div>"
              );
            })
            .join("")
        );

        /* Themes */
        var themes =
          cm.spine_themes || cm.themes || cm.core_themes || cm.story_themes || [];
        var themeList = [];
        if (Array.isArray(themes)) {
          themeList = themes.map(function (t) {
            if (typeof t === "string") return t;
            return t.label || t.name || t.theme || t.id || "";
          });
        } else if (themes && typeof themes === "object") {
          themeList = Object.keys(themes);
        }
        setHtml(
          "theme-cloud",
          themeList.length
            ? themeList
                .filter(Boolean)
                .slice(0, 16)
                .map(function (t) {
                  return '<span class="theme-pill">' + escapeHtml(t) + "</span>";
                })
                .join("")
            : '<span class="help">No spine themes in map yet — generate or load results.</span>'
        );

        /* Characters */
        var chars =
          cm.principals || cm.characters || cm.top_characters || cm.cast || [];
        var charHtml = "";
        if (Array.isArray(chars) && chars.length) {
          charHtml = chars
            .slice(0, 12)
            .map(function (c) {
              if (typeof c === "string") {
                return (
                  '<div class="char-card"><div class="cn">' +
                  escapeHtml(c) +
                  '</div><div class="cr">Principal</div></div>'
                );
              }
              var name = c.name || c.character || c.id || "—";
              var role = c.role || c.arc_role || c.function || c.bio || "Principal";
              var meta =
                c.mentions != null
                  ? c.mentions + " mentions"
                  : c.episodes
                    ? "eps " + (Array.isArray(c.episodes) ? c.episodes.length : c.episodes)
                    : c.importance
                      ? "importance " + c.importance
                      : "";
              return (
                '<div class="char-card"><div class="cn">' +
                escapeHtml(String(name)) +
                '</div><div class="cr">' +
                escapeHtml(String(role).slice(0, 90)) +
                '</div><div class="cm">' +
                escapeHtml(String(meta)) +
                "</div></div>"
              );
            })
            .join("");
        } else {
          charHtml = '<span class="help">No principals listed.</span>';
        }
        setHtml("char-cloud", charHtml);

        /* Arc phases */
        var arcs =
          cm.arc_phases ||
          cm.phases ||
          cm.story_arc ||
          cm.arc ||
          [];
        var arcEl = $("arc-list");
        if (arcEl) {
          if (Array.isArray(arcs) && arcs.length) {
            arcEl.innerHTML = arcs
              .slice(0, 8)
              .map(function (a, i) {
                if (typeof a === "string") {
                  return (
                    '<div class="arc-item"><div class="phase">Phase ' +
                    (i + 1) +
                    '</div><div class="body">' +
                    escapeHtml(a) +
                    "</div></div>"
                  );
                }
                var title =
                  a.label || a.name || a.phase || a.id || "Phase " + (i + 1);
                var body =
                  a.summary ||
                  a.description ||
                  a.desc ||
                  (a.episode_range
                    ? "Episodes " +
                      (Array.isArray(a.episode_range)
                        ? a.episode_range.join("–")
                        : a.episode_range)
                    : "") ||
                  (a.episodes
                    ? "Episodes " +
                      (Array.isArray(a.episodes)
                        ? a.episodes[0] + "–" + a.episodes[a.episodes.length - 1]
                        : a.episodes)
                    : "—");
                return (
                  '<div class="arc-item"><div class="phase">' +
                  escapeHtml(String(title)) +
                  '</div><div class="body">' +
                  escapeHtml(String(body)) +
                  "</div></div>"
                );
              })
              .join("");
          } else {
            arcEl.innerHTML =
              '<div class="help">Arc phases appear when the full continuity map is loaded (all episode loglines).</div>';
          }
        }

        /* Score bars from explain or defaults */
        var weights =
          (explain.score_weights && explain.score_weights.length
            ? explain.score_weights
            : null) || [
            { label: "Hook power", weight: 0.28 },
            { label: "Cliffhanger pull", weight: 0.22 },
            { label: "Emotional charge", weight: 0.14 },
            { label: "Standalone clarity", weight: 0.14 },
            { label: "Series fit", weight: 0.12 },
            { label: "Craft & duration", weight: 0.1 },
          ];
        setHtml(
          "score-bars",
          weights
            .map(function (w) {
              var pct = Math.round((Number(w.weight) || 0) * 100);
              return (
                '<div class="score-row"><div class="label">' +
                escapeHtml(w.label || w.id || "") +
                '</div><div class="track"><div class="fill" style="width:' +
                pct +
                '%"></div></div><div class="pct">' +
                pct +
                "%</div></div>" +
                (w.why
                  ? '<div style="font-size:11.5px;color:var(--faint);margin:-4px 0 6px 120px">' +
                    escapeHtml(w.why) +
                    "</div>"
                  : "")
              );
            })
            .join("")
        );

        var blurb = $("ranking-blurb");
        if (blurb) {
          blurb.textContent =
            "Weights are type-agnostic. Labels (emotional, cliffhanger…) never enter this formula.";
        }

        /* Ranking method notes — plain language cards */
        var rm = data.ranking_method || {};
        var rmEl = $("ranking-method");
        if (rmEl) {
          var keys = Object.keys(rm);
          if (!keys.length) {
            rmEl.innerHTML =
              '<p class="help">Generate or load a deliverable to see pipeline ranking notes.</p>';
          } else {
            rmEl.innerHTML = keys
              .map(function (k) {
                var v = rm[k];
                var text =
                  typeof v === "object" ? JSON.stringify(v, null, 2) : String(v);
                return (
                  '<div style="padding:10px 0;border-bottom:1px solid var(--line)">' +
                  '<div style="font-size:12px;font-weight:800;color:#ffc9cb;margin-bottom:4px">' +
                  escapeHtml(humanKey(k)) +
                  '</div><div style="font-size:12.5px;color:var(--muted);line-height:1.5;white-space:pre-wrap">' +
                  escapeHtml(text) +
                  "</div></div>"
                );
              })
              .join("");
          }
        }

        var lc = data.label_counts || {};
        var rc = data.role_counts || {};
        setHtml(
          "pack-labels",
          Object.keys(lc)
            .map(function (k) {
              return (
                '<span class="tag ' +
                tagClass(k) +
                '">' +
                escapeHtml(k) +
                " · " +
                lc[k] +
                "</span>"
              );
            })
            .join("") || '<span class="help">No pack loaded</span>'
        );
        setHtml(
          "pack-roles",
          Object.keys(rc)
            .map(function (k) {
              return (
                '<span class="tag role">' + escapeHtml(k) + " · " + rc[k] + "</span>"
              );
            })
            .join("") || '<span class="help">No roles assigned</span>'
        );
      })
      .catch(function (e) {
        setHtml(
          "continuity-kv",
          '<div class="empty">' + escapeHtml(e.message || e) + "</div>"
        );
      });
  }

  function renderMarketer() {
    api("/api/marketer")
      .then(function (mk) {
        mk = mk || {};
        var cuts = mk.cut_list || [];
        var cutN = mk.cut_count != null ? mk.cut_count : cuts.length;
        var prot = mk.protected_count != null ? mk.protected_count : "—";
        var kept = mk.kept_count != null ? mk.kept_count : mk.pack_size;
        var pack = mk.pack_size != null ? mk.pack_size : kept;
        var pre = mk.pre_marketer_n != null ? mk.pre_marketer_n : "—";

        setText("mk-cuts", String(cutN));
        setText("mk-prot", String(prot));
        setText("mk-kept", kept != null ? String(kept) : "—");
        setText("mk-pack-size", pack != null ? String(pack) + "  (from ~" + pre + " ranked)" : "—");

        var sumEl = $("mk-summary");
        if (sumEl) {
          sumEl.innerHTML =
            "<strong>What happened on this pack:</strong> " +
            escapeHtml(
              mk.summary ||
                "Marketer Agent reviewed the ranked list, protected heroes, and cut weak-tail promos."
            ) +
            (mk.note
              ? '<span class="tiny">' + escapeHtml(mk.note) + "</span>"
              : '<span class="tiny">Tip: open Priority list to see PROTECTED badges on hero posts.</span>');
        }

        var tb = qs("#cut-table tbody");
        if (!tb) return;
        if (!cuts.length) {
          tb.innerHTML =
            '<tr><td colspan="6"><div class="empty">No cuts on this pack — either Marketer kept everything, or it was not run. Enable “Run Marketer Agent” on Generate and rebuild.</div></td></tr>';
          return;
        }
        tb.innerHTML = cuts
          .map(function (c) {
            var fails = c.fails || c.reasons || c.why_cut || c.cut_reasons || [];
            if (!Array.isArray(fails)) fails = fails ? [fails] : [];
            var raw =
              c.reason || c.marketer_decision || fails.join(" · ") || "weak_craft";
            var reasonText = explainCutReason(raw, fails);
            var labels = c.promo_types || c.labels || [];
            var score =
              c.series_global_score != null
                ? c.series_global_score
                : c.overall_score != null
                  ? c.overall_score
                  : "";
            var was =
              c.old_rank != null
                ? c.old_rank
                : c.campaign_rank != null
                  ? c.campaign_rank
                  : c.post_rank != null
                    ? c.post_rank
                    : "—";
            return (
              "<tr>" +
              "<td>" +
              escapeHtml(String(c.episode != null ? c.episode : "")) +
              '</td><td class="mono">#' +
              escapeHtml(String(was)) +
              '</td><td class="mono">' +
              escapeHtml(String(score)) +
              '</td><td class="cell-text">' +
              escapeHtml(c.hook || "—") +
              '</td><td><div class="cut-badge">Cut</div><div class="cut-reason">' +
              escapeHtml(String(reasonText)) +
              '</div></td><td><div class="tags">' +
              tagsHtml(labels) +
              "</div></td></tr>"
            );
          })
          .join("");
      })
      .catch(function (e) {
        var sumEl = $("mk-summary");
        if (sumEl) sumEl.textContent = e.message || String(e);
      });
  }

  function renderProjects(list, activeId) {
    state.projects = list || [];
    state.activeProjectId = activeId || null;
    state.activeProject =
      state.projects.filter(function (p) {
        return p.id === state.activeProjectId;
      })[0] || null;

    var root = $("project-list");
    if (root) {
      if (!state.projects.length) {
        root.innerHTML =
          '<div class="empty-side">No projects yet.<br/>Create one to upload scripts.</div>';
      } else {
        root.innerHTML = state.projects
          .map(function (p) {
            var st = p.status || "empty";
            return (
              '<div class="project-row">' +
              '<button type="button" class="project-item' +
              (p.id === state.activeProjectId ? " active" : "") +
              '" data-action="select-project" data-project-id="' +
              escapeHtml(p.id) +
              '"><div class="pn">' +
              escapeHtml(p.name || "Untitled") +
              '</div><div class="pm"><span class="st ' +
              escapeHtml(st) +
              '">' +
              escapeHtml(st) +
              "</span><span>" +
              escapeHtml(String(p.script_count != null ? p.script_count : 0)) +
              " scripts</span></div></button>" +
              '<button type="button" class="project-delete" data-action="delete-project" data-project-id="' +
              escapeHtml(p.id) +
              '" title="Delete project" aria-label="Delete project">×</button>' +
              "</div>"
            );
          })
          .join("");
      }
    }

    var name = state.activeProject ? state.activeProject.name : "No project selected";
    setText("topbar-project", name);
    setText(
      "project-pill",
      state.activeProject ? "Project: " + state.activeProject.name : "Project: none"
    );
    setText(
      "stat-scripts",
      state.activeProject && state.activeProject.script_count != null
        ? String(state.activeProject.script_count)
        : "—"
    );

    var empty = $("empty-workspace");
    var ws = $("project-workspace");
    if (state.activeProject) {
      if (empty) empty.hidden = true;
      if (ws) ws.hidden = false;
    } else {
      if (empty) empty.hidden = false;
      if (ws) ws.hidden = true;
    }
  }

  function refreshProjects() {
    return api("/api/projects").then(function (data) {
      renderProjects(data.projects || [], data.active_id);
      return data;
    });
  }

  function openNewProjectModal(show) {
    var m = $("modal-new-project");
    if (!m) return;
    m.hidden = !show;
    if (show && $("new-project-name")) {
      $("new-project-name").value = "";
      $("new-project-name").focus();
    }
  }

  function createProject() {
    var name = (($("new-project-name") && $("new-project-name").value) || "").trim();
    if (!name) {
      alert("Give the project a name (e.g. the microdrama title).");
      return;
    }
    var fd = new FormData();
    fd.append("name", name);
    fd.append(
      "description",
      (($("new-project-desc") && $("new-project-desc").value) || "").trim()
    );
    api("/api/projects", { method: "POST", body: fd })
      .then(function (res) {
        openNewProjectModal(false);
        state.activeProjectId = res.project && res.project.id;
        return refreshProjects().then(function () {
          var box = $("scan-box");
          if (box) box.classList.remove("show");
          setHtml("scan-meta", "");
          setHtml("scan-eps", "");
          setText("stat-campaign", "—");
          setText("stat-pool", "—");
          setText("stat-eps", "—");
          goto("generate");
        });
      })
      .catch(function (e) {
        alert(e.message || String(e));
      });
  }

  function selectProject(projectId) {
    var fd = new FormData();
    fd.append("project_id", projectId);
    api("/api/projects/activate", { method: "POST", body: fd })
      .then(function () {
        return refreshProjects().then(function () {
          return refreshMeta().then(function () {
            if (state.activeProject && state.activeProject.status === "ready") {
              loadCampaign();
            }
          });
        });
      })
      .catch(function (e) {
        alert(e.message || String(e));
      });
  }

  function deleteProject(projectId) {
    var proj = null;
    for (var i = 0; i < state.projects.length; i++) {
      if (state.projects[i].id === projectId) {
        proj = state.projects[i];
        break;
      }
    }
    var name = (proj && proj.name) || "this project";
    if (!confirm('Delete project "' + name + '"? This cannot be undone.')) {
      return;
    }
    var wasActive = state.activeProjectId === projectId;
    api("/api/projects/" + encodeURIComponent(projectId), { method: "DELETE" })
      .then(function () {
        return refreshProjects().then(function () {
          if (wasActive) {
            state.doc = null;
            state.episodePool = null;
            try {
              renderSnapshot({ episodes: [], total: 0 });
            } catch (err) {}
            return refreshMeta();
          }
        });
      })
      .catch(function (e) {
        alert(e.message || String(e));
      });
  }

  function loadModeCached() {
    var fd = new FormData();
    fd.append("mode", state.mode || "hybrid");
    showProgress("Loading demo " + (state.mode || "hybrid") + " results…", 40);
    api("/api/load_mode", { method: "POST", body: fd })
      .then(function (snap) {
        renderSnapshot(snap);
        showProgress("Demo results loaded — for review only", 100);
        return refreshMeta();
      })
      .catch(function (e) {
        showProgress(e.message || String(e), 0);
      });
  }

  function runPipeline() {
    if (!state.activeProjectId) {
      alert("Create or select a project first.");
      return;
    }
    if (!(state.activeProject && state.activeProject.script_count > 0)) {
      alert("Upload a folder of .txt episode scripts first.");
      return;
    }
    var fd = new FormData();
    fd.append("mode", state.mode || "hybrid");
    fd.append("top_k", ($("top-k") && $("top-k").value) || "5");
    fd.append("top_n", ($("top-n") && $("top-n").value) || "25");
    fd.append(
      "use_marketer",
      $("use-marketer") && $("use-marketer").checked ? "1" : "0"
    );

    var btn = $("btn-run");
    if (btn) btn.disabled = true;
    showProgress("Queuing full pipeline…", 5);

    api("/api/projects/" + state.activeProjectId + "/run", {
      method: "POST",
      body: fd,
    })
      .then(function (res) {
        pollJob(res.job_id);
      })
      .catch(function (e) {
        showProgress(e.message || String(e), 0);
        if (btn) btn.disabled = false;
      });
  }

  function generate() {
    runPipeline();
  }

  function pollJob(jobId) {
    api("/api/jobs/" + jobId)
      .then(function (job) {
        showProgress(job.message || job.status, job.progress || 0);
        if (job.status === "done") {
          var btn = $("btn-run");
          if (btn) btn.disabled = false;
          showProgress(job.message || "Complete — opening priority list", 100);
          refreshProjects();
          refreshMeta()
            .then(function () {
              return loadCampaign();
            })
            .then(function () {
              goto("campaign");
            })
            .catch(function () {
              goto("campaign");
            });
          return;
        }
        if (job.status === "error") {
          var b2 = $("btn-run");
          if (b2) b2.disabled = false;
          refreshProjects();
          showProgress(job.error || job.message || "Failed", job.progress || 0);
          return;
        }
        setTimeout(function () {
          pollJob(jobId);
        }, 1400);
      })
      .catch(function (e) {
        var b3 = $("btn-run");
        if (b3) b3.disabled = false;
        showProgress(e.message || String(e), 0);
      });
  }

  function uploadProjectScripts(fileList) {
    if (!state.activeProjectId) {
      alert("Create or select a project first.");
      return;
    }
    if (!fileList || !fileList.length) return;
    var files = Array.prototype.filter.call(fileList, function (f) {
      return /\.txt$/i.test(f.name);
    });
    if (!files.length) {
      alert("No .txt files found in that folder.");
      return;
    }
    var fd = new FormData();
    files.forEach(function (f) {
      var base = f.name.split(/[/\\]/).pop();
      fd.append("files", f, base);
    });
    showProgress("Uploading & parsing " + files.length + " scripts…", 15);
    var box = $("scan-box");
    if (box) box.classList.add("show");
    setHtml("scan-meta", "Uploading…");
    setHtml("scan-eps", "");

    api("/api/projects/" + state.activeProjectId + "/upload", {
      method: "POST",
      body: fd,
    })
      .then(function (res) {
        var parse = res.parse || {};
        setHtml(
          "scan-meta",
          escapeHtml(
            "Saved " +
              res.count +
              " scripts · parsed " +
              (parse.parsed != null ? parse.parsed : res.count) +
              " episode(s)"
          )
        );
        var eps = parse.episodes || [];
        setHtml(
          "scan-eps",
          eps
            .map(function (e) {
              return (
                "Ep " +
                (e.episode != null ? e.episode : "?") +
                " · " +
                (e.file || "") +
                (e.scenes != null ? " · scenes " + e.scenes : "") +
                (e.beats != null ? " · beats " + e.beats : "")
              );
            })
            .join("\n") || (res.saved || []).join("\n")
        );
        showProgress("Scripts ready — pick a mode and run the pipeline", 100);
        return refreshProjects();
      })
      .catch(function (e) {
        setHtml("scan-meta", escapeHtml(e.message || String(e)));
        showProgress(e.message || String(e), 0);
      });
  }

  function wireUploadZone() {
    var zone = $("upload-zone");
    var input = $("folder-input");
    var pick = $("btn-pick-folder");
    if (pick && input) {
      pick.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        input.click();
      });
    }
    if (zone && input) {
      zone.addEventListener("click", function (ev) {
        if (
          ev.target &&
          (ev.target.id === "btn-pick-folder" ||
            (ev.target.closest && ev.target.closest("#btn-pick-folder")))
        ) {
          return;
        }
        input.click();
      });
      zone.addEventListener("dragover", function (ev) {
        ev.preventDefault();
        zone.classList.add("dragover");
      });
      zone.addEventListener("dragleave", function () {
        zone.classList.remove("dragover");
      });
      zone.addEventListener("drop", function (ev) {
        ev.preventDefault();
        zone.classList.remove("dragover");
        if (ev.dataTransfer && ev.dataTransfer.files) {
          uploadProjectScripts(ev.dataTransfer.files);
        }
      });
    }
    if (input) {
      input.addEventListener("change", function () {
        uploadProjectScripts(input.files);
        input.value = "";
      });
    }
    var toggle = $("sidebar-toggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        var sb = $("sidebar");
        if (sb) sb.classList.toggle("open");
      });
    }
  }

  function exportCampaign() {
    window.location.href = "/api/export.xlsx?which=campaign";
  }

  function exportEpisode() {
    var topN = ($("ep-topn") && $("ep-topn").value) || "5";
    var label = ($("ep-label") && $("ep-label").value) || "";
    var q = "which=episode&top_n=" + encodeURIComponent(topN);
    if (label) q += "&label=" + encodeURIComponent(label);
    window.location.href = "/api/export.xlsx?" + q;
  }

  /* Event delegation — never depends on bind order / null nodes */
  document.addEventListener("click", function (ev) {
    var t = ev.target;
    if (!t) return;
    var btn = t.closest ? t.closest("button, [data-action], a.btn") : t;
    if (!btn || !btn.getAttribute) return;

    var view = btn.getAttribute("data-view");
    if (view && btn.closest && btn.closest("#nav-tabs")) {
      ev.preventDefault();
      goto(view);
      return;
    }

    var action = btn.getAttribute("data-action") || btn.id;
    if (action === "new-project" || action === "btn-new-project") {
      ev.preventDefault();
      openNewProjectModal(true);
      return;
    }
    if (action === "create-project-confirm") {
      ev.preventDefault();
      createProject();
      return;
    }
    if (action === "create-project-cancel") {
      ev.preventDefault();
      openNewProjectModal(false);
      return;
    }
    if (action === "select-project") {
      ev.preventDefault();
      var pid = btn.getAttribute("data-project-id");
      if (pid) selectProject(pid);
      return;
    }
    if (action === "delete-project") {
      ev.preventDefault();
      ev.stopPropagation();
      var delId = btn.getAttribute("data-project-id");
      if (delId) deleteProject(delId);
      return;
    }
    if (action === "run-pipeline" || action === "btn-run" || action === "btn-generate" || action === "generate") {
      ev.preventDefault();
      runPipeline();
      return;
    }
    if (action === "load-demo" || action === "btn-load-cached" || action === "load-cached") {
      ev.preventDefault();
      loadModeCached();
      return;
    }
    if (action === "btn-export-campaign" || action === "export-campaign") {
      ev.preventDefault();
      exportCampaign();
      return;
    }
    if (action === "btn-export-episode" || action === "export-episode") {
      ev.preventDefault();
      exportEpisode();
      return;
    }
    if (action === "btn-refresh-eps" || action === "refresh-eps" || action === "refresh-episodes") {
      ev.preventDefault();
      loadEpisodes();
      return;
    }
    if (action === "refresh-campaign") {
      ev.preventDefault();
      loadCampaign();
      return;
    }
    if (action === "goto-campaign") {
      ev.preventDefault();
      goto("campaign");
      return;
    }
    if (action === "goto-episodes") {
      ev.preventDefault();
      goto("episodes");
      return;
    }

    var mode = btn.getAttribute("data-mode");
    if (mode && (btn.classList.contains("mode-card") || action === "pick-mode")) {
      ev.preventDefault();
      state.mode = mode;
      qsa(".mode-card").forEach(function (b) {
        b.classList.toggle("selected", b.getAttribute("data-mode") === state.mode);
      });
      setText("mode-pill", "Mode: " + state.mode);
      setText("live-mode-pill", "Mode: " + state.mode);
      return;
    }

    var path = btn.getAttribute("data-path");
    if (path && btn.classList.contains("folder-item")) {
      ev.preventDefault();
      qsa(".folder-item").forEach(function (b) {
        b.classList.remove("active");
      });
      btn.classList.add("active");
      if ($("folder-path")) $("folder-path").value = path;
      return;
    }

    var lab = btn.getAttribute("data-lab");
    if (lab && btn.closest && btn.closest("#label-cloud")) {
      ev.preventDefault();
      if ($("ep-label")) $("ep-label").value = lab;
      loadEpisodes();
    }
  });

  document.addEventListener("change", function (ev) {
    var el = ev.target;
    if (!el || !el.id) return;
    if (el.id === "file-upload") {
      if (typeof uploadProjectScripts === "function") uploadProjectScripts(el.files);
      return;
    }
    if (el.id === "ep-topn" || el.id === "ep-label" || el.id === "ep-num") {
      loadEpisodes();
      return;
    }
    if (el.id === "camp-label") {
      paintCampaign();
      return;
    }
  });

  document.addEventListener("input", function (ev) {
    var el = ev.target;
    if (!el || !el.id) return;
    if (el.id === "camp-search") paintCampaign();
  });

  window.App = {
    goto: goto,
    init: function () {
      wireUploadZone();
      refreshProjects()
        .then(function () {
          return refreshMeta();
        })
        .then(function () {
          /* ready */
        })
        .catch(function () {
          /* still usable */
        });
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.App.init();
    });
  } else {
    window.App.init();
  }
})();
