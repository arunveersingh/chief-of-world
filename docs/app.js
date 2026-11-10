/* The World — living map. Public repo files only; no trackers. */
(() => {
  "use strict";

  const OWNER = "arunveersingh";
  const REPO = "chief-of-world";
  const BRANCH = "main";
  const RAW = `https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}/`;
  const IST = "Asia/Calcutta";
  const VOTE_RE = /^VOTE\s+(PROP-\d+)\s*:\s*(yes|no|abstain|withdraw)\b/gim;
  const FALLBACK_COLOR = {
    ember: "#ff6b2d", lumen: "#ffd166", wry: "#2ec4b6",
    quill: "#c77dff", forge: "#e09f3e", ash: "#8fa6b8",
  };

  const $ = (id) => document.getElementById(id);
  const state = {
    data: null,
    viewTick: 0,
    playing: false,
    playTimer: null,
    factOffset: 0,
    factTimer: null,
    t0: performance.now(),
    motion: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    sky: { nodes: new Map(), links: [] },
  };

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    ));
  }

  function formatIst(value, withZone = false) {
    if (!value) return "—";
    const d = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    const stamp = new Intl.DateTimeFormat("en-GB", {
      timeZone: IST, year: "numeric", month: "short", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hour12: false,
    }).format(d).replace(",", "");
    return withZone ? `${stamp} IST (Asia/Calcutta)` : `${stamp} IST`;
  }

  function colorOf(id, data) {
    const c = (data.citizens || []).find((x) => x.id === id);
    return (c && c.color) || (data.derived && data.derived.personas && data.derived.personas[id] && data.derived.personas[id].color) || FALLBACK_COLOR[id] || "#ffd56a";
  }
  function glyphOf(id, data) {
    const c = (data.citizens || []).find((x) => x.id === id);
    if (c && c.glyph) return c.glyph;
    const p = data.derived && data.derived.personas && data.derived.personas[id];
    return (p && p.glyph) || "✦";
  }
  function nameOf(id, data) {
    if (id === "fund") return "The jar";
    const c = (data.citizens || []).find((x) => x.id === id);
    return c ? c.name : id[0].toUpperCase() + id.slice(1);
  }
  function cssVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  async function fetchJson(url) {
    const res = await fetch(url, { cache: "no-cache" });
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return res.json();
  }
  async function fetchText(url) {
    const res = await fetch(url, { cache: "no-cache" });
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return res.text();
  }
  async function firstJson(urls) {
    let last;
    for (const u of urls) {
      try { return await fetchJson(u); } catch (e) { last = e; }
    }
    throw last || new Error("no data");
  }

  function firstParagraph(text, limit = 280) {
    const cleaned = String(text || "")
      .replace(/```[\s\S]*?```/g, " ")
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l && !l.startsWith("#") && !l.startsWith("---"));
    const joined = cleaned.join(" ").replace(/\s+/g, " ").trim();
    if (joined.length <= limit) return joined;
    return joined.slice(0, limit - 1).replace(/\s+\S*$/, "") + "…";
  }

  function parseAction(text, id, tick) {
    const votes = {};
    const re = new RegExp(VOTE_RE.source, VOTE_RE.flags);
    let m;
    while ((m = re.exec(text))) votes[m[1].toUpperCase()] = m[2].toLowerCase();
    let body = "";
    const section = text.match(/##\s+(Public statement|What I say|Statement)[^\n]*\n([\s\S]*?)(?=^##\s|\Z)/im);
    if (section) body = section[2];
    else {
      const bold = text.match(/\*\*Public statement\*\*\s*([\s\S]*?)(?=^\*\*Actions\*\*|^##\s|\*\*Votes\*\*|\Z)/im);
      body = bold ? bold[1] : text;
    }
    return {
      tick,
      file: `agents/${id}/actions/tick-${tick}.md`,
      summary: firstParagraph(body, 280),
      votes,
      url: `https://github.com/${OWNER}/${REPO}/blob/${BRANCH}/agents/${id}/actions/tick-${tick}.md`,
    };
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    const btn = $("theme-toggle");
    btn.textContent = theme === "light" ? "Dark" : "Light";
    btn.setAttribute("aria-pressed", theme === "light" ? "true" : "false");
    try { localStorage.setItem("world-theme", theme); } catch (_) { /* ignore */ }
    if (state.data) {
      drawGini(state.data);
      drawWater(state.data);
      paintStars(true);
    }
  }

  function initTheme() {
    let theme = null;
    try { theme = localStorage.getItem("world-theme"); } catch (_) { /* ignore */ }
    if (theme !== "light" && theme !== "dark") {
      theme = "dark";
    }
    applyTheme(theme);
    $("theme-toggle").addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
      applyTheme(next);
    });
  }

  function overlayLive(data, live) {
    const world = live.state, budget = live.budget, activity = live.activity, citizensFile = live.citizens;
    if (!world) return data;
    const header = data.header || (data.header = {});
    if (world.tick != null) header.resolved_tick = world.tick;
    if (world.world_date) header.world_date = world.world_date;
    const resources = world.shared_resources || {};
    if (resources.compute_credits_total_in_circulation != null) header.credits_in_circulation = resources.compute_credits_total_in_circulation;
    if (resources.voluntary_project_fund != null) header.fund_balance = resources.voluntary_project_fund;
    if (budget) {
      header.ticks_used_today = budget.ticks_used_today;
      header.max_ticks_per_day = budget.max_ticks_per_day;
      header.budget_date = budget.date;
    }
    if (activity) {
      header.last_meaningful_commit = activity.last_meaningful_commit;
      header.consecutive_inactive_days = activity.consecutive_inactive_days || 0;
      const inactive = header.consecutive_inactive_days;
      const threshold = header.extinction_threshold || 7;
      header.days_until_extinction = Math.max(0, threshold - inactive);
      const extinct = (world.agents || []).some((a) => a.status === "extinct");
      header.status = (inactive >= threshold || extinct) ? "extinct" : (inactive > 0 ? "at_risk" : "alive");
    }
    if (citizensFile && citizensFile.open_tick != null) header.open_tick = citizensFile.open_tick;
    if (Array.isArray(world.agents)) {
      const byId = Object.fromEntries(world.agents.map((a) => [a.id, a]));
      for (const c of data.citizens || []) {
        const a = byId[c.id];
        if (!a) continue;
        c.credits = a.credits;
        c.reputation = a.reputation;
        c.status = a.status;
      }
    }
    if (world.proposals) {
      data.proposals = Object.entries(world.proposals).map(([id, meta]) => ({
        id, yes: [], no: [], abstain: [], ...meta,
        url: meta.file ? `https://github.com/${OWNER}/${REPO}/blob/${BRANCH}/${meta.file}` : undefined,
      })).sort((a, b) => Number((b.id.match(/\d+/) || [0])[0]) - Number((a.id.match(/\d+/) || [0])[0]));
    }
    if (Array.isArray(world.institutions)) {
      const fund = world.institutions.find((i) => i.id === "voluntary_project_fund");
      if (fund) data.fund = fund;
    }
    if (data.derived && data.derived.counters) {
      const c = data.derived.counters;
      c.resolved_tick = header.resolved_tick;
      c.open_tick = header.open_tick;
      c.tick = header.open_tick || header.resolved_tick;
      c.fund = header.fund_balance;
      c.credits = header.credits_in_circulation;
      c.laws = (data.laws_in_force || []).length || c.laws;
    }
    return data;
  }

  async function refreshOpenActions(data) {
    const tick = data.header && data.header.open_tick;
    const resolved = data.header && data.header.resolved_tick;
    if (!tick || !(tick > resolved)) return;
    await Promise.all((data.citizens || []).map(async (c) => {
      try {
        const text = await fetchText(`${RAW}agents/${c.id}/actions/tick-${tick}.md`);
        c.last_action = parseAction(text, c.id, tick);
      } catch (_) { /* not filed yet */ }
    }));
  }

  function frameAt(data, tick) {
    const frames = (data.derived && data.derived.frames) || [];
    let best = frames[0] || null;
    for (const f of frames) {
      if (f.tick <= tick) best = f;
    }
    return best;
  }

  function latestTick(data) {
    const frames = (data.derived && data.derived.frames) || [];
    if (frames.length) return frames[frames.length - 1].tick;
    return data.header ? data.header.resolved_tick : 0;
  }

  /* ---------- stars ---------- */
  const starState = { dots: [], w: 0, h: 0 };
  function paintStars(reset) {
    const canvas = $("stars");
    const stage = $("stage");
    if (!canvas || !stage) return;
    const dpr = window.devicePixelRatio || 1;
    const w = stage.clientWidth, h = stage.clientHeight;
    if (reset || w !== starState.w || h !== starState.h) {
      starState.w = w; starState.h = h;
      canvas.width = w * dpr; canvas.height = h * dpr;
      canvas.style.width = w + "px"; canvas.style.height = h + "px";
      const n = Math.min(120, Math.floor((w * h) / 9000));
      starState.dots = Array.from({ length: n }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        r: Math.random() * 1.2 + 0.3,
        a: Math.random() * 0.5 + 0.15,
        s: Math.random() * 0.15 + 0.02,
      }));
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const c = cssVar("--gold", "#ffd56a");
    for (const d of starState.dots) {
      ctx.beginPath();
      ctx.fillStyle = c;
      ctx.globalAlpha = d.a;
      ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }
  function driftStars() {
    if (!state.motion) return;
    for (const d of starState.dots) {
      d.y += d.s;
      if (d.y > starState.h) d.y = 0;
    }
    paintStars(false);
  }

  /* ---------- constellation ---------- */
  function layout(data) {
    const ids = (data.citizens || []).map((c) => c.id);
    const cx = 500, cy = 268, r = 212;
    const pos = { fund: { x: cx, y: cy } };
    ids.forEach((id, i) => {
      const a = -Math.PI / 2 + (i * 2 * Math.PI) / ids.length;
      pos[id] = { x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r * 0.92, phase: i * 1.1 };
    });
    return pos;
  }

  function radiusFor(credits) {
    const n = credits == null ? 0 : Number(credits);
    return 20 + Math.sqrt(Math.max(0, n)) * 6.2;
  }

  function buildSky(data) {
    const svg = $("sky");
    const pos = layout(data);
    state.sky.pos = pos;
    const ns = "http://www.w3.org/2000/svg";
    svg.innerHTML = "";
    const defs = document.createElementNS(ns, "defs");
    defs.innerHTML = `
      <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3.5" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>`;
    svg.appendChild(defs);
    const linkG = document.createElementNS(ns, "g");
    linkG.setAttribute("id", "links");
    const nodeG = document.createElementNS(ns, "g");
    nodeG.setAttribute("id", "nodes");
    svg.appendChild(linkG);
    svg.appendChild(nodeG);

    const frame = frameAt(data, state.viewTick) || {};
    const credits = frame.credits || {};
    const fundBal = frame.fund != null ? frame.fund : (data.header && data.header.fund_balance) || 0;

    const open = data.header && data.header.open_tick;
    const resolved = data.header && data.header.resolved_tick;
    const liveView = state.viewTick >= latestTick(data);

    function addNode(id, label, glyph, color, creditsVal, kind) {
      const p = pos[id];
      const rad = radiusFor(kind === "fund" ? (creditsVal || 0) * 1.2 + 4 : creditsVal);
      const g = document.createElementNS(ns, "g");
      g.setAttribute("class", "node");
      g.setAttribute("data-id", id);
      g.setAttribute("tabindex", "0");
      g.setAttribute("role", "button");
      g.setAttribute("aria-label", `${label}, ${creditsVal ?? 0} credits`);
      const ring = document.createElementNS(ns, "circle");
      ring.setAttribute("class", "ring");
      ring.setAttribute("cx", p.x); ring.setAttribute("cy", p.y);
      ring.setAttribute("r", rad + 8);
      ring.setAttribute("stroke", color);
      const core = document.createElementNS(ns, "circle");
      core.setAttribute("class", "core");
      core.setAttribute("cx", p.x); core.setAttribute("cy", p.y);
      core.setAttribute("r", rad);
      core.setAttribute("fill", color);
      core.setAttribute("fill-opacity", "0.22");
      core.setAttribute("stroke", color);
      core.setAttribute("stroke-width", "2.5");
      const emoji = document.createElementNS(ns, "text");
      emoji.setAttribute("x", p.x); emoji.setAttribute("y", p.y + 2);
      emoji.setAttribute("text-anchor", "middle");
      emoji.setAttribute("dominant-baseline", "middle");
      emoji.setAttribute("font-size", kind === "fund" ? "22" : "20");
      emoji.textContent = glyph;
      const name = document.createElementNS(ns, "text");
      name.setAttribute("x", p.x); name.setAttribute("y", p.y + rad + 18);
      name.setAttribute("text-anchor", "middle");
      name.setAttribute("fill", cssVar("--text", "#f6f1e6"));
      name.setAttribute("font-size", "13");
      name.setAttribute("font-weight", "800");
      name.textContent = label;
      const num = document.createElementNS(ns, "text");
      num.setAttribute("class", "credit-label");
      num.setAttribute("x", p.x); num.setAttribute("y", p.y + rad + 32);
      num.setAttribute("text-anchor", "middle");
      num.setAttribute("fill", cssVar("--muted", "#9a96a6"));
      num.setAttribute("font-size", "11");
      num.textContent = kind === "fund" ? `${creditsVal} in the jar` : `${creditsVal ?? "—"} cr`;
      g.append(ring, core, emoji, name, num);
      const citizen = (data.citizens || []).find((c) => c.id === id);
      const acted = liveView && citizen && citizen.last_action && open && citizen.last_action.tick === open && open > resolved;
      if (acted) g.classList.add("pulsing");
      g.addEventListener("click", () => openDossier(id));
      g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openDossier(id); } });
      nodeG.appendChild(g);
      state.sky.nodes.set(id, { g, p, ring, core, num, color, kind });
    }

    addNode("fund", "The jar", "🏺", cssVar("--gold", "#ffd56a"), fundBal, "fund");
    for (const c of data.citizens || []) {
      addNode(c.id, c.name, c.glyph || glyphOf(c.id, data), c.color || colorOf(c.id, data), credits[c.id] != null ? credits[c.id] : c.credits, "citizen");
    }

    // Default links: votes, fund flows, distrust. Relations appear on hover.
    const links = ((data.derived && data.derived.graph_links) || []).filter((l) => l.kind !== "relation");
    state.sky.links = links;
    drawLinks(data);
    hookHover(data);
  }

  function drawLinks(data) {
    const svg = $("sky");
    const linkG = svg.querySelector("#links");
    if (!linkG) return;
    const pos = state.sky.pos;
    const maxVote = Math.max(1, ...state.sky.links.filter((l) => l.kind === "vote").map((l) => l.weight));
    linkG.innerHTML = "";
    const ns = "http://www.w3.org/2000/svg";
    for (const l of state.sky.links) {
      const a = pos[l.from], b = pos[l.to];
      if (!a || !b) continue;
      const path = document.createElementNS(ns, "path");
      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      const cx = 500, cy = 268;
      const k = l.kind === "vote" ? 0.18 : 0.08;
      const qx = mx + (cx - mx) * k, qy = my + (cy - my) * k;
      path.setAttribute("d", `M ${a.x} ${a.y} Q ${qx} ${qy} ${b.x} ${b.y}`);
      path.setAttribute("class", `link ${l.kind}`);
      if (l.kind === "vote") {
        path.setAttribute("stroke", cssVar("--cyan", "#3ee0c5"));
        path.setAttribute("stroke-width", String(1.2 + (l.weight / maxVote) * 3.5));
        path.setAttribute("opacity", String(0.25 + (l.weight / maxVote) * 0.5));
      } else if (l.kind === "distrust") {
        path.setAttribute("stroke", cssVar("--danger", "#ff5d6c"));
        path.setAttribute("stroke-width", "1.6");
      } else if (l.kind === "deposit") {
        path.setAttribute("stroke", cssVar("--gold", "#ffd56a"));
        path.setAttribute("stroke-width", String(1 + l.weight * 0.4));
      } else if (l.kind === "grant") {
        path.setAttribute("stroke", cssVar("--ok", "#5ee0a0"));
        path.setAttribute("stroke-width", String(1.4 + l.weight * 0.5));
      } else {
        path.setAttribute("stroke", cssVar("--muted", "#9a96a6"));
        path.setAttribute("stroke-width", "1.1");
      }
      path.setAttribute("data-kind", l.kind);
      linkG.appendChild(path);
    }
  }

  function hookHover(data) {
    const svg = $("sky");
    const all = (data.derived && data.derived.graph_links) || [];
    svg.querySelectorAll(".node").forEach((g) => {
      const id = g.getAttribute("data-id");
      const show = () => {
        const extra = all.filter((l) => l.kind === "relation" && (l.from === id || l.to === id));
        const base = ((data.derived && data.derived.graph_links) || []).filter((l) => l.kind !== "relation");
        state.sky.links = base.concat(extra);
        drawLinks(data);
      };
      const hide = () => {
        state.sky.links = ((data.derived && data.derived.graph_links) || []).filter((l) => l.kind !== "relation");
        drawLinks(data);
      };
      g.addEventListener("mouseenter", show);
      g.addEventListener("focus", show);
      g.addEventListener("mouseleave", hide);
      g.addEventListener("blur", hide);
    });
  }

  function driftNodes() {
    if (!state.motion || !state.sky.pos) return;
    const t = (performance.now() - state.t0) / 1000;
    for (const [id, rec] of state.sky.nodes) {
      if (id === "fund") continue;
      const ox = Math.sin(t * 0.6 + rec.p.phase) * 5;
      const oy = Math.cos(t * 0.5 + rec.p.phase) * 4;
      rec.g.setAttribute("transform", `translate(${ox} ${oy})`);
    }
  }

  function updateSkySizes(data) {
    const frame = frameAt(data, state.viewTick) || {};
    const credits = frame.credits || {};
    const fundBal = frame.fund != null ? frame.fund : 0;
    const open = data.header && data.header.open_tick;
    const resolved = data.header && data.header.resolved_tick;
    const liveView = state.viewTick >= latestTick(data);
    for (const [id, rec] of state.sky.nodes) {
      const val = id === "fund" ? fundBal : credits[id];
      const rad = radiusFor(id === "fund" ? (val || 0) * 1.2 + 4 : val);
      rec.core.setAttribute("r", rad);
      rec.ring.setAttribute("r", rad + 8);
      const label = rec.g.querySelector(".credit-label");
      if (label) label.textContent = id === "fund" ? `${val ?? "—"} in the jar` : `${val ?? "—"} cr`;
      const name = rec.g.querySelectorAll("text")[1];
      if (name) name.setAttribute("y", rec.p.y + rad + 18);
      if (label) label.setAttribute("y", rec.p.y + rad + 32);
      const citizen = (data.citizens || []).find((c) => c.id === id);
      const acted = liveView && citizen && citizen.last_action && open && citizen.last_action.tick === open && open > resolved;
      rec.g.classList.toggle("pulsing", !!acted);
    }
  }

  /* ---------- hud / counters / ticker ---------- */
  function renderHud(data) {
    const h = data.header || {};
    const badge = $("status-badge");
    const label = { alive: "Alive", at_risk: "At risk", extinct: "Extinct" }[h.status] || h.status || "…";
    badge.textContent = label;
    badge.className = "live " + (h.status || "");
    const used = h.ticks_used_today, cap = h.max_ticks_per_day;
    $("hud-meta").textContent = used != null ? `${used} / ${cap} ticks today` : "";
    $("foot-gen").textContent = `Updated ${formatIst(data.generated_at || h.head_commit_at, true)}`;
  }

  function renderTicker(data) {
    const items = (data.derived && data.derived.drama) || [];
    const bits = items.map((d) => `<span><b>Tick ${d.tick}</b> — ${escapeHtml(d.text)}</span>`);
    // Duplicate for a seamless loop
    $("ticker-track").innerHTML = bits.concat(bits).join("");
  }

  function renderCounters(data) {
    const frame = frameAt(data, state.viewTick) || {};
    const live = state.viewTick >= latestTick(data);
    const c = (data.derived && data.derived.counters) || {};
    const tickLabel = live && c.open_tick && c.open_tick > c.resolved_tick
      ? `${c.open_tick}`
      : String(state.viewTick);
    const tickSub = live && c.open_tick && c.open_tick > c.resolved_tick ? "open tick" : "tick";
    const laws = live ? c.laws : (frame.laws_in_force || []).length;
    const items = [
      { n: tickLabel, k: tickSub },
      { n: laws, k: "laws in force" },
      { n: c.proposals ?? "—", k: "proposals" },
      { n: frame.fund ?? c.fund ?? "—", k: "in the jar" },
      { n: frame.circulation ?? c.credits ?? "—", k: "credits loose" },
      { n: c.days_alive ?? "—", k: "days alive" },
    ];
    $("counters").innerHTML = items.map((it) =>
      `<div class="counter"><span class="n">${escapeHtml(String(it.n))}</span><span class="k">${escapeHtml(it.k)}</span></div>`
    ).join("");
  }

  /* ---------- facts ---------- */
  function renderFacts(data) {
    const facts = (data.derived && data.derived.facts) || [];
    if (!facts.length) { $("facts").innerHTML = ""; return; }
    const show = 4;
    const start = state.factOffset % facts.length;
    const slice = [];
    for (let i = 0; i < Math.min(show, facts.length); i++) slice.push(facts[(start + i) % facts.length]);
    $("facts").innerHTML = slice.map((f) => `
      <article class="fact" data-subject="${escapeHtml(f.subject || "")}">
        <div class="icon">${escapeHtml(f.icon || "✦")}</div>
        <h3>${escapeHtml(f.title)}</h3>
        <p>${escapeHtml(f.text)}</p>
      </article>`).join("");
    $("facts").querySelectorAll(".fact").forEach((el) => {
      el.addEventListener("click", () => {
        const s = el.getAttribute("data-subject");
        if (s && (data.citizens || []).some((c) => c.id === s)) openDossier(s);
        else if (s && String(s).startsWith("tick-")) {
          const t = Number(String(s).slice(5));
          if (!Number.isNaN(t)) setViewTick(t);
        }
      });
    });
  }

  /* ---------- theater ---------- */
  function renderTheater(data) {
    const max = latestTick(data);
    const slider = $("tick-slider");
    slider.min = 0; slider.max = max; slider.value = state.viewTick;
    const marks = [];
    for (let t = 0; t <= max; t++) {
      marks.push(`<button type="button" data-tick="${t}" class="${t === state.viewTick ? "on" : ""}">${t}</button>`);
    }
    $("tick-marks").innerHTML = marks.join("");
    updateHeadline(data);
  }

  function updateHeadline(data) {
    const frame = frameAt(data, state.viewTick);
    const live = state.viewTick >= latestTick(data);
    const open = data.header && data.header.open_tick;
    const resolved = data.header && data.header.resolved_tick;
    let text = (frame && frame.headline) || `Tick ${state.viewTick}`;
    if (live && open && open > resolved) text = `Tick ${open} is open — ${text}`;
    else text = `Tick ${state.viewTick} — ${text}`;
    $("tick-headline").textContent = text;
    $("tick-marks").querySelectorAll("button").forEach((b) => {
      b.classList.toggle("on", Number(b.dataset.tick) === state.viewTick);
    });
    $("tick-slider").value = state.viewTick;
    $("play").textContent = state.playing ? "Pause" : (state.viewTick >= latestTick(data) ? "Replay" : "Play");
    $("play").classList.toggle("playing", state.playing);
  }

  function setViewTick(t) {
    const data = state.data;
    const max = latestTick(data);
    state.viewTick = Math.max(0, Math.min(max, t));
    updateHeadline(data);
    renderCounters(data);
    updateSkySizes(data);
    renderRace(data);
    drawGini(data);
    drawWater(data);
    renderLaws(data);
    $("hint").style.opacity = "0.35";
  }

  function togglePlay() {
    if (state.playing) {
      state.playing = false;
      clearTimeout(state.playTimer);
      updateHeadline(state.data);
      return;
    }
    if (state.viewTick >= latestTick(state.data)) setViewTick(0);
    state.playing = true;
    updateHeadline(state.data);
    const step = () => {
      if (!state.playing) return;
      if (state.viewTick >= latestTick(state.data)) {
        state.playing = false;
        updateHeadline(state.data);
        return;
      }
      setViewTick(state.viewTick + 1);
      state.playTimer = setTimeout(step, 900);
    };
    state.playTimer = setTimeout(step, 200);
  }

  /* ---------- charts ---------- */
  function renderRace(data) {
    const frame = frameAt(data, state.viewTick) || {};
    const credits = { ...(frame.credits || {}) };
    const hist = (data.derived && data.derived.frames) || data.credit_history || [];
    let max = 1;
    for (const f of hist) {
      for (const v of Object.values(f.credits || {})) if (v > max) max = v;
    }
    const rows = (data.citizens || []).slice().sort((a, b) => (credits[b.id] || 0) - (credits[a.id] || 0));
    $("race").innerHTML = rows.map((c) => {
      const v = credits[c.id] ?? 0;
      const pct = Math.max(2, (v / max) * 100);
      const col = c.color || colorOf(c.id, data);
      return `<div class="row">
        <span class="who">${escapeHtml((c.glyph || "") + " " + c.name)}</span>
        <div class="track"><i style="width:${pct}%;background:${col}"></i></div>
        <span class="n">${v}</span>
      </div>`;
    }).join("");
  }

  function drawGini(data) {
    const canvas = $("gini-chart");
    if (!canvas) return;
    const frames = (data.derived && data.derived.frames) || [];
    const cur = frameAt(data, state.viewTick);
    $("gini-num").textContent = cur && cur.gini != null ? cur.gini.toFixed(2) : "—";
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth || 520, h = 160;
    canvas.width = w * dpr; canvas.height = h * dpr;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    if (!frames.length) return;
    const pad = { l: 28, r: 10, t: 12, b: 24 };
    const ys = frames.map((f) => f.gini || 0);
    const yMax = Math.max(0.3, Math.ceil(Math.max(...ys) * 10) / 10);
    const xAt = (i) => pad.l + (i / Math.max(1, frames.length - 1)) * (w - pad.l - pad.r);
    const yAt = (v) => pad.t + (1 - v / yMax) * (h - pad.t - pad.b);
    const muted = cssVar("--muted", "#9a96a6");
    const gold = cssVar("--gold", "#ffd56a");
    const line = cssVar("--line", "rgba(255,255,255,0.09)");
    ctx.strokeStyle = line; ctx.lineWidth = 1;
    ctx.font = "10px sans-serif"; ctx.fillStyle = muted;
    [0, yMax / 2, yMax].forEach((v) => {
      ctx.beginPath(); ctx.moveTo(pad.l, yAt(v)); ctx.lineTo(w - pad.r, yAt(v)); ctx.stroke();
      ctx.fillText(v.toFixed(2), 2, yAt(v) + 3);
    });
    frames.forEach((f, i) => ctx.fillText(String(f.tick), xAt(i) - 3, h - 6));
    const visible = frames.filter((f) => f.tick <= state.viewTick);
    if (!visible.length) return;
    ctx.beginPath();
    visible.forEach((f, i) => {
      const x = xAt(frames.indexOf(f)), y = yAt(f.gini || 0);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    const lastI = frames.findIndex((f) => f.tick === visible[visible.length - 1].tick);
    ctx.lineTo(xAt(lastI), yAt(0));
    ctx.lineTo(xAt(0), yAt(0));
    ctx.closePath();
    ctx.fillStyle = gold; ctx.globalAlpha = 0.18; ctx.fill(); ctx.globalAlpha = 1;
    ctx.beginPath();
    visible.forEach((f, i) => {
      const x = xAt(frames.indexOf(f)), y = yAt(f.gini || 0);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = gold; ctx.lineWidth = 2.2; ctx.stroke();
    const now = visible[visible.length - 1];
    ctx.beginPath();
    ctx.arc(xAt(frames.indexOf(now)), yAt(now.gini || 0), 4, 0, Math.PI * 2);
    ctx.fillStyle = gold; ctx.fill();
  }

  function renderHeat(data) {
    const vm = data.derived && data.derived.vote_matrix;
    if (!vm) { $("heat").innerHTML = ""; return; }
    const ids = vm.ids || [];
    const max = Math.max(1, ...ids.flatMap((a) => ids.map((b) => (a === b ? 0 : (vm.co_yes[a] && vm.co_yes[a][b]) || 0))));
    let html = `<div class="heat" style="grid-template-columns: 1.6rem repeat(${ids.length}, auto)">`;
    html += `<div></div>`;
    ids.forEach((id) => { html += `<div class="lab" title="${escapeHtml(nameOf(id, data))}">${glyphOf(id, data)}</div>`; });
    ids.forEach((row) => {
      html += `<div class="lab">${glyphOf(row, data)}</div>`;
      ids.forEach((col) => {
        if (row === col) {
          html += `<div class="cell" style="background:transparent;color:var(--faint)">·</div>`;
          return;
        }
        const v = (vm.co_yes[row] && vm.co_yes[row][col]) || 0;
        const t = v / max;
        const bg = `color-mix(in srgb, ${colorOf(row, data)} ${Math.round(t * 85)}%, rgba(255,255,255,0.06))`;
        html += `<div class="cell" style="background:${bg}" title="${escapeHtml(nameOf(row, data))} &amp; ${escapeHtml(nameOf(col, data))}: ${v} shared yes votes">${v || ""}</div>`;
      });
    });
    html += `</div>`;
    $("heat").innerHTML = html;
  }

  function renderFunnel(data) {
    const f = (data.derived && data.derived.funnel) || {};
    const rows = [
      { k: "Filed", v: f.filed || 0, c: cssVar("--gold", "#ffd56a") },
      { k: "Passed", v: f.passed || 0, c: cssVar("--ok", "#5ee0a0") },
      { k: "Withdrawn", v: f.withdrawn || 0, c: cssVar("--muted", "#9a96a6") },
      { k: "Still open", v: f.open || 0, c: cssVar("--cyan", "#3ee0c5") },
    ];
    const max = Math.max(1, f.filed || 0);
    $("funnel").innerHTML = rows.map((r) => `
      <div class="row"><span>${escapeHtml(r.k)}</span>
        <div class="bar"><i style="width:${(r.v / max) * 100}%;background:${r.c}"></i></div>
        <strong>${r.v}</strong></div>`).join("");
  }

  function renderStreaks(data) {
    const streaks = (data.derived && data.derived.streaks) || {};
    $("streaks").innerHTML = (data.citizens || []).map((c) => {
      const s = streaks[c.id] || { streak: 0, present: [], expected: 0 };
      const dots = [];
      const last = s.expected || latestTick(data);
      for (let t = 1; t <= last; t++) {
        const on = (s.present || []).includes(t);
        dots.push(`<span class="dot ${on ? "on" : ""}" style="--c:${c.color || colorOf(c.id, data)}" title="Tick ${t}${on ? " · present" : " · missing"}"></span>`);
      }
      return `<div class="row">
        <span class="who">${escapeHtml((c.glyph || "") + " " + c.name)}</span>
        <div class="dots">${dots.join("")}</div>
        <span class="streak-n">${s.streak} in a row</span>
      </div>`;
    }).join("");
  }

  function drawWater(data) {
    const canvas = $("water-chart");
    if (!canvas) return;
    const rows = ((data.derived && data.derived.waterfall) || []).filter((r) => r.tick <= state.viewTick);
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth || 520, h = 200;
    canvas.width = w * dpr; canvas.height = h * dpr;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    $("water-legend").innerHTML = `<span><i style="background:${cssVar("--ok","#5ee0a0")}"></i>in</span><span><i style="background:${cssVar("--danger","#ff5d6c")}"></i>out</span><span><i style="background:${cssVar("--gold","#ffd56a")}"></i>balance</span>`;
    if (!rows.length) return;
    const pad = { l: 28, r: 10, t: 14, b: 26 };
    const yMax = Math.max(8, ...((data.derived && data.derived.waterfall) || []).map((r) => Math.max(r.end, r.start, r.start + r.inflow)));
    const bw = (w - pad.l - pad.r) / Math.max(rows.length, 1) * 0.62;
    const gap = (w - pad.l - pad.r) / Math.max(rows.length, 1);
    const yAt = (v) => pad.t + (1 - v / yMax) * (h - pad.t - pad.b);
    const muted = cssVar("--muted", "#9a96a6");
    const ok = cssVar("--ok", "#5ee0a0");
    const danger = cssVar("--danger", "#ff5d6c");
    const gold = cssVar("--gold", "#ffd56a");
    ctx.strokeStyle = cssVar("--line", "rgba(255,255,255,0.09)");
    ctx.fillStyle = muted; ctx.font = "10px sans-serif";
    ctx.beginPath(); ctx.moveTo(pad.l, yAt(0)); ctx.lineTo(w - pad.r, yAt(0)); ctx.stroke();
    rows.forEach((r, i) => {
      const x = pad.l + i * gap + (gap - bw) / 2;
      if (r.inflow) {
        ctx.fillStyle = ok;
        ctx.fillRect(x, yAt(r.start + r.inflow), bw, yAt(r.start) - yAt(r.start + r.inflow));
      }
      if (r.outflow) {
        ctx.fillStyle = danger;
        const top = r.start + r.inflow;
        ctx.fillRect(x, yAt(top), bw, yAt(top - r.outflow) - yAt(top));
      }
      ctx.fillStyle = gold;
      ctx.fillRect(x, yAt(r.end) - 2, bw, 4);
      ctx.fillStyle = muted;
      ctx.fillText(String(r.tick), x + bw / 2 - 3, h - 8);
    });
  }

  function renderLaws(data) {
    const frame = frameAt(data, state.viewTick) || {};
    const force = new Set(frame.laws_in_force || data.laws_in_force || []);
    const passedThis = new Set(frame.laws_passed_this_tick || []);
    const laws = data.laws || [];
    $("laws-track").innerHTML = laws.map((l) => {
      const on = force.has(l.id);
      const now = passedThis.has(l.id);
      const cls = "law-chip" + (on ? "" : " dim") + (now ? " on" : "");
      const sun = l.sunset_tick ? ` · sunsets after ${l.sunset_tick}` : "";
      return `<button type="button" class="${cls}" data-id="${escapeHtml(l.id)}" title="${escapeHtml((l.excerpt || "") + sun)}"><b>${escapeHtml(l.id)}</b> ${escapeHtml(l.title || "")}</button>`;
    }).join("");
    $("laws-track").querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => openLaw(btn.getAttribute("data-id")));
    });
  }

  /* ---------- sheets ---------- */
  function openDossier(id) {
    const data = state.data;
    const dlg = $("dossier");
    const body = $("dossier-body");
    if (id === "fund") {
      const fund = data.fund || {};
      const contrib = Object.entries(fund.contributors || {}).map(([k, v]) => `${nameOf(k, data)} ${v}`).join(" · ");
      const grants = (fund.grants || []).map((g) => {
        const short = (g.name || g.proposal || "grant").split("(")[0].trim();
        return `${short} → ${nameOf(g.recipient, data)} (${g.amount})`;
      }).join(" · ");
      body.innerHTML = `
        <h2>🏺 The jar</h2>
        <p class="tagline">Voluntary project fund</p>
        <div class="metrics">
          <div><strong>${fund.balance ?? data.header.fund_balance ?? "—"}</strong><span>balance</span></div>
          <div><strong>${(fund.grants || []).length}</strong><span>grants paid</span></div>
        </div>
        <p class="quote">${escapeHtml(contrib ? "In: " + contrib : "No contributors yet.")}</p>
        <p class="quote">${escapeHtml(grants || "No grants yet.")}</p>`;
      dlg.showModal();
      return;
    }
    const c = (data.citizens || []).find((x) => x.id === id);
    if (!c) return;
    const act = c.last_action;
    const votes = act && act.votes
      ? Object.entries(act.votes).map(([p, v]) => `<span class="tag ${escapeHtml(v)}">${escapeHtml(p)} ${escapeHtml(v)}</span>`).join("")
      : "";
    const streak = data.derived && data.derived.streaks && data.derived.streaks[id];
    const frame = frameAt(data, latestTick(data)) || {};
    const cr = c.credits != null ? c.credits : (frame.credits || {})[id];
    body.innerHTML = `
      <h2>${escapeHtml((c.glyph || "") + " " + c.name)}</h2>
      <p class="tagline">${escapeHtml(c.tagline || "")}</p>
      <div class="metrics">
        <div><strong>${cr ?? "—"}</strong><span>credits</span></div>
        <div><strong>${c.reputation ?? "—"}</strong><span>reputation</span></div>
        <div><strong>${(streak && streak.streak) || "—"}</strong><span>streak</span></div>
      </div>
      ${act && act.summary ? `<p class="quote">“${escapeHtml(act.summary)}”</p>` : "<p class='quote'>No statement filed this tick.</p>"}
      <div class="tags">${votes}</div>
      <p style="margin:0.8rem 0 0">${act && act.url ? `<a href="${act.url}">Read the full action</a>` : ""} · <a href="${c.profile_url}">profile</a></p>`;
    dlg.showModal();
  }

  function openLaw(id) {
    const law = (state.data.laws || []).find((l) => l.id === id);
    if (!law) return;
    const dlg = $("dossier");
    const sun = law.sunset_note || (law.sunset_tick ? `Sunsets after tick ${law.sunset_tick}.` : "");
    $("dossier-body").innerHTML = `
      <h2>${escapeHtml(law.id)}</h2>
      <p class="tagline">${escapeHtml(law.title || "")}${law.in_force ? " · in force" : " · retired"}</p>
      <p class="quote">${escapeHtml(law.excerpt || "")}</p>
      ${sun ? `<p class="tagline">${escapeHtml(sun)}</p>` : ""}
      ${law.url ? `<p><a href="${law.url}">Read the law</a></p>` : ""}`;
    dlg.showModal();
  }

  /* ---------- render + load ---------- */
  function renderAll(data) {
    state.data = data;
    state.viewTick = latestTick(data);
    renderHud(data);
    renderTicker(data);
    buildSky(data);
    renderCounters(data);
    renderFacts(data);
    renderTheater(data);
    renderRace(data);
    drawGini(data);
    renderHeat(data);
    renderFunnel(data);
    renderStreaks(data);
    drawWater(data);
    renderLaws(data);
    paintStars(true);
    if (state.factTimer) clearInterval(state.factTimer);
    const facts = (data.derived && data.derived.facts) || [];
    if (facts.length > 4 && state.motion) {
      state.factTimer = setInterval(() => {
        state.factOffset = (state.factOffset + 4) % facts.length;
        renderFacts(state.data);
      }, 8000);
    }
  }

  function bind() {
    $("play").addEventListener("click", togglePlay);
    $("tick-slider").addEventListener("input", (e) => {
      if (state.playing) togglePlay();
      setViewTick(Number(e.target.value));
    });
    $("tick-marks").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-tick]");
      if (!b) return;
      if (state.playing) togglePlay();
      setViewTick(Number(b.dataset.tick));
    });
    $("ticker-track").addEventListener("click", (e) => {
      const s = e.target.closest("span");
      if (!s) return;
      const m = s.textContent && s.textContent.match(/^Tick\s+(\d+)/);
      if (m) setViewTick(Number(m[1]));
    });
    window.addEventListener("resize", () => {
      paintStars(true);
      if (state.data) { drawGini(state.data); drawWater(state.data); }
    });
    $("hint").addEventListener("click", () => { $("hint").style.opacity = "0"; });
    const loop = () => {
      driftStars();
      driftNodes();
      requestAnimationFrame(loop);
    };
    if (state.motion) requestAnimationFrame(loop);
  }

  async function load() {
    const err = $("load-error");
    err.hidden = true;
    try {
      const localFirst = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
      const snapshot = localFirst
        ? await firstJson(["./data/world.json", RAW + "docs/data/world.json"])
        : await firstJson([RAW + "docs/data/world.json", "./data/world.json"]);
      const live = {};
      await Promise.all([
        fetchJson(RAW + "world/state.json").then((j) => { live.state = j; }).catch(() => {}),
        fetchJson(RAW + "world/budget.json").then((j) => { live.budget = j; }).catch(() => {}),
        fetchJson(RAW + "world/activity.json").then((j) => { live.activity = j; }).catch(() => {}),
        fetchJson(RAW + "world/citizens.json").then((j) => { live.citizens = j; }).catch(() => {}),
      ]);
      const data = overlayLive(snapshot, live);
      await refreshOpenActions(data);
      renderAll(data);
    } catch (e) {
      err.hidden = false;
      err.textContent = "Could not load the world. " + (e && e.message ? e.message : "Try again.");
    }
  }

  initTheme();
  bind();
  load();
})();
