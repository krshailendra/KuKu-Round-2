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
