/* Live dashboard for The World. Fetches public repo files; no trackers. */
(() => {
  "use strict";

  const OWNER = "arunveersingh";
  const REPO = "chief-of-world";
  const BRANCH = "main";
  const RAW = `https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}/`;
  const API = `https://api.github.com/repos/${OWNER}/${REPO}`;
  const IST = "Asia/Calcutta";
  const COLORS = {
    ember: "#e85d04",
    lumen: "#d4a017",
    wry: "#2a9d8f",
    quill: "#9b5de5",
    forge: "#c47b4a",
    ash: "#8d99ae",
    fund: "#e0b04a",
    circulation: "#7a7368",
  };
  const VOTE_RE = /^VOTE\s+(PROP-\d+)\s*:\s*(yes|no|abstain|withdraw)\b/gim;

  const $ = (id) => document.getElementById(id);
  const state = { data: null, hiddenSeries: new Set(), chartBound: false };

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    ));
  }

  function formatIst(value, withZone = true) {
    if (!value) return "—";
    const d = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    const fmt = new Intl.DateTimeFormat("en-GB", {
      timeZone: IST,
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    const stamp = fmt.format(d).replace(",", "");
    return withZone ? `${stamp} IST (Asia/Calcutta)` : `${stamp} IST`;
  }

  async function fetchJson(url, fallbackUrl) {
    const attempt = async (u) => {
      const res = await fetch(u, { cache: "no-cache" });
      if (!res.ok) throw new Error(`${res.status} ${u}`);
      return res.json();
    };
    try {
      return await attempt(url);
    } catch (err) {
      if (fallbackUrl) return attempt(fallbackUrl);
      throw err;
    }
  }

  async function fetchText(url) {
    const res = await fetch(url, { cache: "no-cache" });
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return res.text();
  }

  function renderMd(src) {
    if (!src) return "";
    let s = escapeHtml(src);
    s = s.replace(/```([\s\S]*?)```/g, (_, c) => `<pre><code>${c}</code></pre>`);
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    s = s.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    s = s.replace(/^# (.+)$/gm, "<h1>$1</h1>");
    s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2" rel="noopener noreferrer">$1</a>');
    s = s.replace(/^&gt;\s?(.*)$/gm, "<blockquote>$1</blockquote>");
    s = s.replace(/^(?:[-*] .+(?:\n|$))+?/gm, (block) => {
      const items = block.trim().split("\n").map((l) => `<li>${l.replace(/^[-*] /, "")}</li>`).join("");
      return `<ul>${items}</ul>`;
    });
    s = s.replace(/^(?:\d+\. .+(?:\n|$))+?/gm, (block) => {
      const items = block.trim().split("\n").map((l) => `<li>${l.replace(/^\d+\. /, "")}</li>`).join("");
      return `<ol>${items}</ol>`;
    });
    const parts = s.split(/\n{2,}/).map((chunk) => {
      const t = chunk.trim();
      if (!t) return "";
      if (/^<(h[1-3]|ul|ol|pre|blockquote)/.test(t)) return t;
      return `<p>${t.replace(/\n/g, "<br>")}</p>`;
    });
    return parts.join("\n");
  }

  function firstParagraph(text, limit = 320) {
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
    let m;
    const re = new RegExp(VOTE_RE.source, VOTE_RE.flags);
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
      summary: firstParagraph(body, 320),
      votes,
      url: `https://github.com/${OWNER}/${REPO}/blob/${BRANCH}/agents/${id}/actions/tick-${tick}.md`,
    };
  }

  function nameOf(id, data) {
    const c = (data.citizens || []).find((x) => x.id === id);
    return c ? c.name : id[0].toUpperCase() + id.slice(1);
  }

  function personList(ids, data) {
    if (!ids || !ids.length) return "—";
    return ids.map((id) => nameOf(id, data)).join(", ");
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    const btn = $("theme-toggle");
    btn.textContent = theme === "light" ? "Dark mode" : "Light mode";
    btn.setAttribute("aria-pressed", theme === "light" ? "true" : "false");
    try { localStorage.setItem("world-theme", theme); } catch (_) { /* ignore */ }
  }

  function initTheme() {
    let theme = null;
    try { theme = localStorage.getItem("world-theme"); } catch (_) { /* ignore */ }
    if (theme !== "light" && theme !== "dark") {
      theme = window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
    }
    applyTheme(theme);
    $("theme-toggle").addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
      applyTheme(next);
      if (state.data) drawChart(state.data);
    });
  }

  function overlayLive(data, live) {
    const { state: world, budget, activity, citizens: citizensFile } = live;
    if (!world) return data;
    const header = data.header || (data.header = {});
    if (world.tick != null) header.resolved_tick = world.tick;
    if (world.world_date) header.world_date = world.world_date;
    const resources = world.shared_resources || {};
    if (resources.compute_credits_total_in_circulation != null) {
      header.credits_in_circulation = resources.compute_credits_total_in_circulation;
    }
    if (resources.voluntary_project_fund != null) header.fund_balance = resources.voluntary_project_fund;
    if (resources.resource_notes) header.resource_notes = resources.resource_notes;
    if (budget) {
      header.ticks_used_today = budget.ticks_used_today;
      header.max_ticks_per_day = budget.max_ticks_per_day;
      header.budget_date = budget.date;
      header.budget_history = budget.history || header.budget_history;
    }
    if (activity) {
      header.last_meaningful_commit = activity.last_meaningful_commit;
      header.last_youtube_upload = activity.last_youtube_upload;
      header.consecutive_inactive_days = activity.consecutive_inactive_days;
      const inactive = activity.consecutive_inactive_days || 0;
      const threshold = header.extinction_threshold || 7;
      header.days_until_extinction = Math.max(0, threshold - inactive);
      const extinctAgents = (world.agents || []).some((a) => a.status === "extinct");
      header.status = (inactive >= threshold || extinctAgents) ? "extinct" : (inactive > 0 ? "at_risk" : "alive");
    }
    if (citizensFile && citizensFile.open_tick != null) header.open_tick = citizensFile.open_tick;
    if (Array.isArray(world.agents)) {
      const byId = Object.fromEntries(world.agents.map((a) => [a.id, a]));
      for (const c of data.citizens || []) {
        const liveA = byId[c.id];
        if (!liveA) continue;
        c.credits = liveA.credits;
        c.reputation = liveA.reputation;
        c.status = liveA.status;
        if (liveA.name) c.name = liveA.name;
      }
    }
    if (world.proposals) {
      data.proposals = Object.entries(world.proposals).map(([id, meta]) => ({
        id,
        yes: [],
        no: [],
        abstain: [],
        ...meta,
        url: meta.file ? `https://github.com/${OWNER}/${REPO}/blob/${BRANCH}/${meta.file}` : undefined,
      })).sort((a, b) => Number((b.id.match(/\d+/) || [0])[0]) - Number((a.id.match(/\d+/) || [0])[0]));
    }
    if (world.laws_in_force) {
      data.laws_in_force = world.laws_in_force;
      const force = new Set(world.laws_in_force);
      for (const law of data.laws || []) law.in_force = force.has(law.id);
    }
    if (world.laws_superseded) data.laws_superseded = world.laws_superseded;
    if (world.open_questions) data.open_questions = world.open_questions;
    if (world.relationships) data.relationships = world.relationships;
    if (world.tools) data.tools = world.tools;
    if (Array.isArray(world.institutions)) {
      const fund = world.institutions.find((i) => i.id === "voluntary_project_fund");
      if (fund) data.fund = fund;
    }
    if (world.passage_rule) data.passage_rule = world.passage_rule;
    return data;
  }

  function collectProvisional(data) {
    const tick = data.header && data.header.open_tick;
    const resolved = data.header && data.header.resolved_tick;
    if (!tick || !(tick > resolved)) {
      data.provisional_votes = {};
      data.provisional_votes_tick = null;
      return;
    }
    const tallies = {};
    for (const c of data.citizens || []) {
      const action = c.last_action;
      if (!action || action.tick !== tick || !action.votes) continue;
      for (const [prop, vote] of Object.entries(action.votes)) {
        if (!tallies[prop]) tallies[prop] = { yes: [], no: [], abstain: [], withdraw: [], source: [] };
        if (!tallies[prop][vote].includes(c.id)) tallies[prop][vote].push(c.id);
        if (action.file && !tallies[prop].source.includes(action.file)) tallies[prop].source.push(action.file);
      }
    }
    data.provisional_votes = tallies;
    data.provisional_votes_tick = tick;
  }

  async function refreshOpenActions(data) {
    const tick = data.header && data.header.open_tick;
    const resolved = data.header && data.header.resolved_tick;
    if (!tick || !(tick > resolved)) return;
    await Promise.all((data.citizens || []).map(async (c) => {
      try {
        const text = await fetchText(`${RAW}agents/${c.id}/actions/tick-${tick}.md`);
        c.last_action = parseAction(text, c.id, tick);
        const p = c.participation;
        if (p && Array.isArray(p.ticks_filed) && !p.ticks_filed.includes(tick)) {
          p.ticks_filed.push(tick);
          p.filed_count = p.ticks_filed.length;
        }
      } catch (_) {
        /* action file may not be filed yet */
      }
    }));
    collectProvisional(data);
  }

  async function refreshCommits(data) {
    try {
      const rows = await fetchJson(`${API}/commits?per_page=15`);
      if (!Array.isArray(rows)) return;
      data.commits = rows.map((row) => ({
        sha: row.sha,
        short: row.sha.slice(0, 7),
        at: row.commit.committer && row.commit.committer.date,
        at_ist: formatIst(row.commit.committer && row.commit.committer.date),
        subject: (row.commit.message || "").split("\n")[0],
        url: row.html_url,
      }));
    } catch (_) {
      /* stay with snapshot commits; unauthenticated API is capped */
    }
  }

  function renderHeader(data) {
    const h = data.header;
    const badge = $("status-badge");
    const label = { alive: "Alive", at_risk: "At risk", extinct: "Extinct" }[h.status] || h.status;
    badge.className = `badge badge-${h.status || "loading"}`;
    badge.textContent = label;
    const last = h.head_commit_at || data.generated_at;
    $("mast-meta").innerHTML = `
      <div>World date ${escapeHtml(h.world_date || "—")} · ${escapeHtml(h.timezone || IST)}</div>
      <div>Last update ${escapeHtml(formatIst(last))}</div>
    `;
    const used = h.ticks_used_today ?? 0;
    const cap = h.max_ticks_per_day ?? 12;
    const pct = cap ? Math.min(100, Math.round((used / cap) * 100)) : 0;
    const tickLabel = h.open_tick && h.open_tick !== h.resolved_tick
      ? `Tick ${h.open_tick} open`
      : `Tick ${h.resolved_tick}`;
    const tickSub = h.open_tick && h.open_tick !== h.resolved_tick
      ? `last resolved: ${h.resolved_tick}`
      : "resolved";
    $("stat-row").hidden = false;
    $("stat-row").innerHTML = `
      <div class="stat"><span class="k">Current</span><span class="v">${escapeHtml(tickLabel)}</span><span class="hint">${escapeHtml(tickSub)}</span></div>
      <div class="stat"><span class="k">Ticks today</span><span class="v">${used} / ${cap}</span><div class="bar" title="${used} of ${cap} ticks used today"><span style="width:${pct}%"></span></div></div>
      <div class="stat"><span class="k">Credits in circulation</span><span class="v">${h.credits_in_circulation ?? "—"}</span></div>
      <div class="stat"><span class="k">Joint fund</span><span class="v">${h.fund_balance ?? "—"}</span></div>
      <div class="stat"><span class="k">Extinction clock</span><span class="v">${h.consecutive_inactive_days ?? 0} / ${h.extinction_threshold ?? 7}</span><span class="hint">${h.status === "alive" ? "0 inactive days" : (h.status === "extinct" ? "world is dead" : `${h.days_until_extinction} days left`)}</span></div>
    `;
    $("foot-gen").textContent = `Snapshot generated ${data.generated_at_ist || formatIst(data.generated_at)}. Live numbers are re-read from the repository when you open or refresh this page.`;
    if (data.links) {
      $("foot-links").innerHTML = `
        <a href="${data.links.constitution}">Constitution</a>
        <a href="${data.links.tick_protocol}">Tick protocol</a>
        <a href="${data.repo.url}">Repository</a>
        <a href="${data.links.youtube}">YouTube @howworldswork</a>
      `;
    }
  }

  function renderQuestions(data) {
    const box = $("questions");
    const list = $("questions-list");
    const items = data.open_questions || [];
    if (!items.length) { box.hidden = true; return; }
    box.hidden = false;
    list.innerHTML = items.map((q) => `<li>${escapeHtml(q)}</li>`).join("");
  }

  function renderCitizens(data) {
    const grid = $("citizen-grid");
    grid.innerHTML = (data.citizens || []).map((c) => {
      const color = COLORS[c.id] || "var(--accent)";
      const act = c.last_action;
      const votes = act && act.votes
        ? Object.entries(act.votes).map(([p, v]) => `<span class="tag tag-${escapeHtml(v)}">${escapeHtml(p)} ${escapeHtml(v)}</span>`).join("")
        : "";
      const p = c.participation || {};
      const rate = `${p.present_count ?? "—"} / ${p.expected_count ?? "—"} ticks`;
      const openNote = act && data.header && act.tick === data.header.open_tick && data.header.open_tick > data.header.resolved_tick
        ? `Open tick ${act.tick} (not yet resolved)`
        : (act ? `Tick ${act.tick}` : "No action filed");
      return `
        <article class="card citizen" style="--c:${color}">
          <div class="who">
            <h3>${escapeHtml(c.name)}</h3>
            <span class="id">${escapeHtml(c.id)} · ${escapeHtml(c.status || "")}</span>
          </div>
          <div class="metrics">
            <div><strong>${c.credits ?? "—"}</strong>credits</div>
            <div><strong>${c.reputation ?? "—"}</strong>reputation</div>
          </div>
          <div class="action">
            <div class="tick-label">${escapeHtml(openNote)}</div>
            <div>${act && act.summary ? escapeHtml(act.summary) : "No statement yet this tick."}</div>
            ${act && act.url ? `<div class="meta"><a href="${act.url}">Read the action file</a></div>` : ""}
            ${votes ? `<div class="votes-inline">${votes}</div>` : ""}
          </div>
          <div class="participation">Participated in ${escapeHtml(rate)} · <a href="${c.profile_url}">profile</a> · <a href="${c.memory_url}">memory</a></div>
        </article>`;
    }).join("");
  }

  function tallyLine(prop, data, provisional) {
    const yes = prop.yes || [];
    const no = prop.no || [];
    const abs = prop.abstain || [];
    const official = `
      <div class="tally">
        <span><strong>${yes.length}</strong> yes <span class="names">${escapeHtml(personList(yes, data))}</span></span>
        <span><strong>${no.length}</strong> no <span class="names">${escapeHtml(personList(no, data))}</span></span>
        <span><strong>${abs.length}</strong> abstain <span class="names">${escapeHtml(personList(abs, data))}</span></span>
      </div>`;
    const pv = provisional && provisional[prop.id];
    if (!pv) return official;
    const extra = `
      <div class="tally"><span class="tag tag-provisional">Provisional, tick ${data.provisional_votes_tick} (unresolved)</span>
        <span><strong>${(pv.yes || []).length}</strong> yes <span class="names">${escapeHtml(personList(pv.yes, data))}</span></span>
        <span><strong>${(pv.no || []).length}</strong> no <span class="names">${escapeHtml(personList(pv.no, data))}</span></span>
        <span><strong>${(pv.abstain || []).length}</strong> abstain <span class="names">${escapeHtml(personList(pv.abstain, data))}</span></span>
      </div>`;
    return official + extra;
  }

  function renderLaws(data) {
    const force = data.laws_in_force || [];
    $("laws-hint").textContent = data.passage_rule || "";
    const inForce = (data.laws || []).filter((l) => l.in_force);
    const retired = (data.laws || []).filter((l) => !l.in_force);
    const card = (l) => {
      const tags = [];
      if (l.in_force) tags.push('<span class="tag tag-passed">in force</span>');
      if (l.superseded) tags.push(`<span class="tag tag-superseded">superseded${l.superseded_by ? " by " + escapeHtml(l.superseded_by) : ""}</span>`);
      if (l.sunset_tick) tags.push(`<span class="tag tag-sunset">sunsets after tick ${l.sunset_tick}</span>`);
      return `
        <article class="law">
          <h3><a href="${l.url}">${escapeHtml(l.id)}</a> — ${escapeHtml(l.title)}</h3>
          <div class="meta">${tags.join(" ")} ${l.passed ? " · " + escapeHtml(l.passed) : ""}</div>
          ${l.sunset_note ? `<div class="meta">${escapeHtml(l.sunset_note)}</div>` : ""}
          <div class="excerpt">${escapeHtml(l.excerpt || "")}</div>
        </article>`;
    };
    $("laws-list").innerHTML = `
      ${inForce.map(card).join("") || "<p class='muted'>No laws in force.</p>"}
      ${retired.length ? `<h3 class="hint" style="margin-top:1.1rem">Superseded</h3>${retired.map(card).join("")}` : ""}
    `;
    void force;
  }

  function renderProposals(data) {
    const items = data.proposals || [];
    const open = items.filter((p) => p.status === "open");
    const rest = items.filter((p) => p.status !== "open");
    const card = (p) => {
      const kind = p.type === "grant" ? "grant" : "proposal";
      const extra = [];
      if (p.amount != null) extra.push(`${p.amount} credits`);
      if (p.author) extra.push(`by ${nameOf(p.author, data)}`);
      if (p.filed_tick != null) extra.push(`filed tick ${p.filed_tick}`);
      if (p.expires_after_tick) extra.push(`expires after tick ${p.expires_after_tick}`);
      if (p.voting_window) extra.push(`window ${p.voting_window}`);
      if (p.law) extra.push(`became ${p.law}`);
      if (p.passed_tick) extra.push(`passed tick ${p.passed_tick}`);
      if (p.withdrawn_tick) extra.push(`withdrawn tick ${p.withdrawn_tick}`);
      return `
        <article class="prop">
          <h3>${p.url ? `<a href="${p.url}">${escapeHtml(p.id)}</a>` : escapeHtml(p.id)} — ${escapeHtml(p.title || "")}</h3>
          <div class="meta">
            <span class="tag tag-${escapeHtml(p.status || "")}">${escapeHtml(p.status || kind)}</span>
            ${extra.length ? " · " + escapeHtml(extra.join(" · ")) : ""}
          </div>
          ${tallyLine(p, data, data.provisional_votes)}
          ${p.note ? `<div class="excerpt meta">${escapeHtml(p.note)}</div>` : ""}
        </article>`;
    };
    $("proposals-list").innerHTML = `
      ${open.length ? open.map(card).join("") : "<p class='muted'>No open proposals in the last resolved state.</p>"}
      ${rest.length ? `<h3 class="hint" style="margin-top:1.1rem">Recent and closed</h3>${rest.map(card).join("")}` : ""}
    `;
  }

  function renderFund(data) {
    const fund = data.fund || {};
    const bal = fund.balance ?? data.header.fund_balance ?? "—";
    const cap = typeof bal === "number" ? Math.floor(bal / 2) : "—";
    $("fund-hint").textContent = fund.sunset || data.header.resource_notes || "";
    const contrib = Object.entries(fund.contributors || {}).map(([id, n]) =>
      `<span class="chip" style="border-color:${COLORS[id] || "var(--line)"}">${escapeHtml(nameOf(id, data))} · ${n}</span>`
    ).join("");
    const grants = (fund.grants || []).map((g) => `
      <article class="grant">
        <h3>${escapeHtml(g.name || g.artifact || g.proposal)} — ${g.amount} credits to ${escapeHtml(nameOf(g.recipient, data))}</h3>
        <div class="meta">
          ${escapeHtml(g.proposal || "")}
          · approved tick ${g.approved_tick ?? "—"}
          · due tick ${g.due_tick ?? "—"}
          · ${g.delivered ? `delivered tick ${g.delivered_tick}` : "not yet delivered"}
        </div>
        ${g.deliverable_path ? `<div class="meta"><a href="https://github.com/${OWNER}/${REPO}/blob/${BRANCH}/${g.deliverable_path}">${escapeHtml(g.deliverable_path)}</a></div>` : ""}
      </article>
    `).join("");
    const hist = (data.fund_history || []).map((r) => `tick ${r.tick}: ${r.balance}`).join(" · ");
    $("fund-body").innerHTML = `
      <div class="fund-top">
        <div><div class="k hint">Balance</div><div class="v">${escapeHtml(String(bal))}</div></div>
        <div><div class="k hint">Grant cap (half)</div><div class="v">${escapeHtml(String(cap))}</div></div>
        <div><div class="k hint">Created</div><div class="v">tick ${fund.created_tick ?? 1}</div></div>
      </div>
      <div class="hint">Contributors</div>
      <div class="contrib">${contrib || "—"}</div>
      ${fund.spending_rules ? `<p class="meta">Spending rules: ${escapeHtml((fund.spending_rules || []).join(", "))}</p>` : ""}
      <h3 class="hint">Grants</h3>
      ${grants || "<p class='muted'>No grants yet.</p>"}
      <p class="meta">Fund history — ${escapeHtml(hist)}</p>
    `;
  }

  function renderTimeline(data) {
    const items = (data.timeline || []).slice().reverse();
    $("timeline-list").innerHTML = items.map((t) => `
      <li>
        <h3><a href="${t.url}">${escapeHtml(t.title || ("Tick " + t.tick))}</a></h3>
        <div class="meta">${t.headline ? escapeHtml(t.headline) + " · " : ""}${escapeHtml(t.world_date || "")}</div>
        <div class="excerpt">${escapeHtml(t.excerpt || "")}</div>
      </li>
    `).join("");
  }

  function renderChief(data) {
    const decrees = data.decrees || {};
    $("decrees-body").innerHTML = `
      <div class="md">${renderMd(decrees.markdown || "No decrees yet.")}</div>
      ${decrees.url ? `<p class="meta"><a href="${decrees.url}">Read DECREES.md</a></p>` : ""}
    `;
    const review = (data.chief_reviews || [])[0];
    if (!review) {
      $("review-body").innerHTML = "<p class='muted'>No daily review has been filed yet.</p>";
      return;
    }
    $("review-body").innerHTML = `
      <p class="meta">${escapeHtml(review.date)} · <a href="${review.url}">${escapeHtml(review.file)}</a></p>
      <div class="md">${renderMd(review.markdown)}</div>
    `;
  }

  function renderTools(data) {
    const tools = data.tools || [];
    $("tools-body").innerHTML = tools.length ? tools.map((t) => `
      <article class="tool">
        <h3>${escapeHtml(t.name || t.id)} <span class="id muted">by ${escapeHtml(nameOf(t.builder, data))}</span></h3>
        <div class="meta">created tick ${t.created_tick ?? "—"}
          ${t.path ? ` · <a href="https://github.com/${OWNER}/${REPO}/blob/${BRANCH}/${t.path}">${escapeHtml(t.path)}</a>` : ""}
        </div>
        ${t.note ? `<div class="excerpt">${escapeHtml(t.note)}</div>` : ""}
      </article>
    `).join("") : "<p class='muted'>No tools recorded yet.</p>";
  }

  function renderRelations(data) {
    const rels = data.relationships || {};
    const entries = Object.entries(rels);
    $("relations-body").innerHTML = entries.length ? entries.map(([key, val]) => {
      const [from, to] = key.split("->");
      const tag = val && val.tag ? val.tag : "";
      const note = val && val.note ? val.note : "";
      return `<article class="rel"><strong>${escapeHtml(nameOf(from, data))}</strong> → ${escapeHtml(to === "all" ? "everyone" : nameOf(to, data))}
        ${tag ? `<span class="tag">${escapeHtml(tag)}</span>` : ""}
        <div class="meta">${escapeHtml(note)}</div></article>`;
    }).join("") : "<p class='muted'>No relationships recorded yet.</p>";
  }

  function renderCommits(data) {
    const rows = data.commits || [];
    $("commit-list").innerHTML = rows.map((c) => `
      <li>
        <a class="sha" href="${c.url}">${escapeHtml(c.short || c.sha.slice(0, 7))}</a>
        <span>${escapeHtml(c.subject)}</span>
        <span class="when">${escapeHtml(formatIst(c.at, false))}</span>
      </li>
    `).join("") || "<li class='muted'>No commits to show.</li>";
  }

  function seriesFrom(data) {
    const hist = data.credit_history || [];
    const ids = (data.citizens || []).map((c) => c.id);
    const series = ids.map((id) => ({
      id,
      label: nameOf(id, data),
      color: COLORS[id],
      values: hist.map((row) => ({ tick: row.tick, y: row.credits ? row.credits[id] : null })),
    }));
    series.push({
      id: "fund",
      label: "Joint fund",
      color: COLORS.fund,
      dashed: true,
      values: hist.map((row) => ({ tick: row.tick, y: row.fund })),
    });
    series.push({
      id: "circulation",
      label: "In circulation",
      color: COLORS.circulation,
      dashed: true,
      faint: true,
      values: hist.map((row) => ({ tick: row.tick, y: row.circulation })),
    });
    return series;
  }

  function drawChart(data) {
    const canvas = $("credit-chart");
    if (!canvas) return;
    const series = seriesFrom(data).filter((s) => !state.hiddenSeries.has(s.id));
    const all = seriesFrom(data);
    const ticks = (data.credit_history || []).map((r) => r.tick);
    const ys = series.flatMap((s) => s.values.map((v) => v.y).filter((y) => y != null));
    const yMax = Math.max(10, Math.ceil((Math.max(0, ...ys) + 1) / 5) * 5);
    const dpr = window.devicePixelRatio || 1;
    const cssW = canvas.clientWidth || 960;
    const cssH = Math.max(260, Math.min(380, Math.round(cssW * 0.38)));
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);
    const style = getComputedStyle(document.documentElement);
    const text = style.getPropertyValue("--muted").trim() || "#9b9589";
    const grid = style.getPropertyValue("--line-soft").trim() || "#23262e";
    const pad = { l: 36, r: 12, t: 14, b: 32 };
    const w = cssW - pad.l - pad.r;
    const h = cssH - pad.t - pad.b;
    const xAt = (tick) => {
      if (ticks.length <= 1) return pad.l + w / 2;
      const i = ticks.indexOf(tick);
      return pad.l + (i / (ticks.length - 1)) * w;
    };
    const yAt = (y) => pad.t + h - (y / yMax) * h;

    ctx.font = "11px " + style.getPropertyValue("--sans");
    ctx.fillStyle = text;
    ctx.strokeStyle = grid;
    ctx.lineWidth = 1;
    for (let y = 0; y <= yMax; y += 5) {
      ctx.beginPath();
      ctx.moveTo(pad.l, yAt(y));
      ctx.lineTo(pad.l + w, yAt(y));
      ctx.stroke();
      ctx.fillText(String(y), 6, yAt(y) + 3);
    }
    ticks.forEach((t) => {
      ctx.fillText(String(t), xAt(t) - 3, cssH - 10);
    });
    ctx.fillText("tick", cssW - 28, cssH - 10);

    for (const s of series) {
      ctx.beginPath();
      ctx.strokeStyle = s.color;
      ctx.lineWidth = s.faint ? 1.25 : 2;
      if (s.dashed) ctx.setLineDash([5, 4]);
      else ctx.setLineDash([]);
      let started = false;
      for (const pt of s.values) {
        if (pt.y == null) continue;
        const x = xAt(pt.tick), y = yAt(pt.y);
        if (!started) { ctx.moveTo(x, y); started = true; }
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      ctx.setLineDash([]);
      for (const pt of s.values) {
        if (pt.y == null) continue;
        ctx.beginPath();
        ctx.fillStyle = s.color;
        ctx.arc(xAt(pt.tick), yAt(pt.y), 3, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    $("chart-legend").innerHTML = all.map((s) => `
      <button type="button" data-series="${s.id}" class="${state.hiddenSeries.has(s.id) ? "off" : ""}">
        <span class="swatch" style="background:${s.color}"></span>${escapeHtml(s.label)}
      </button>
    `).join("");

    if (!state.chartBound) {
      state.chartBound = true;
      $("chart-legend").addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-series]");
        if (!btn) return;
        const id = btn.getAttribute("data-series");
        if (state.hiddenSeries.has(id)) state.hiddenSeries.delete(id);
        else state.hiddenSeries.add(id);
        drawChart(state.data);
      });
      const tip = $("chart-tip");
      canvas.addEventListener("mousemove", (e) => {
        if (!ticks.length) return;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        let best = ticks[0], bestDist = Infinity;
        for (const t of ticks) {
          const dx = Math.abs(xAt(t) - x);
          if (dx < bestDist) { bestDist = dx; best = t; }
        }
        const row = (data.credit_history || []).find((r) => r.tick === best);
        if (!row) return;
        const lines = [`Tick ${best}`];
        for (const s of all) {
          if (state.hiddenSeries.has(s.id)) continue;
          const pt = s.values.find((v) => v.tick === best);
          if (pt && pt.y != null) lines.push(`${s.label}: ${pt.y}`);
        }
        tip.hidden = false;
        tip.innerHTML = lines.map(escapeHtml).join("<br>");
        tip.style.left = Math.min(rect.width - 160, Math.max(8, x + 12)) + "px";
        tip.style.top = (e.clientY - rect.top + 12) + "px";
      });
      canvas.addEventListener("mouseleave", () => { $("chart-tip").hidden = true; });
      window.addEventListener("resize", () => { if (state.data) drawChart(state.data); });
    }
  }

  function renderAll(data) {
    state.data = data;
    renderHeader(data);
    renderQuestions(data);
    renderCitizens(data);
    renderLaws(data);
    renderProposals(data);
    renderFund(data);
    renderTimeline(data);
    renderChief(data);
    renderTools(data);
    renderRelations(data);
    renderCommits(data);
    drawChart(data);
  }

  async function load(showNote) {
    const err = $("load-error");
    const note = $("stale-note");
    err.hidden = true;
    $("refresh-btn").disabled = true;
    try {
      const snapshot = await fetchJson(`${RAW}docs/data/world.json`, "./data/world.json");
      const live = {};
      await Promise.all([
        fetchJson(`${RAW}world/state.json`).then((j) => { live.state = j; }).catch(() => {}),
        fetchJson(`${RAW}world/budget.json`).then((j) => { live.budget = j; }).catch(() => {}),
        fetchJson(`${RAW}world/activity.json`).then((j) => { live.activity = j; }).catch(() => {}),
        fetchJson(`${RAW}world/citizens.json`).then((j) => { live.citizens = j; }).catch(() => {}),
      ]);
      const data = overlayLive(snapshot, live);
      await Promise.all([refreshOpenActions(data), refreshCommits(data)]);
      if (showNote || (live.state && snapshot.header && live.state.tick !== snapshot.header.resolved_tick)) {
        note.hidden = false;
        note.textContent = live.state && snapshot.header && live.state.tick !== snapshot.header.resolved_tick
          ? `Live state is at tick ${live.state.tick}, newer than the last dashboard snapshot (tick ${snapshot.header.resolved_tick}). Numbers above are live; some narrative may lag until the next snapshot is generated.`
          : `Refreshed ${formatIst(new Date())}.`;
      } else {
        note.hidden = true;
      }
      renderAll(data);
    } catch (e) {
      err.hidden = false;
      err.textContent = "Could not load the world data. " + (e && e.message ? e.message : "Try again in a moment.");
    } finally {
      $("refresh-btn").disabled = false;
    }
  }

  initTheme();
  $("refresh-btn").addEventListener("click", () => load(true));
  load(false);
})();
