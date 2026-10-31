(function () {
  const { el, clear, frame, seg, predict } = EE;
  const pct = (x, d = 0) => (100 * x).toFixed(d) + "%";
  const COLORS = { whole: "var(--ink-faint)", oat: "var(--accent)", almond: "var(--teal)", left: "var(--bad)" };

  function stacked(label, parts, total) {
    return el("div", { class: "bar-row" },
      el("span", { text: label }),
      el("div", { class: "bar-track" }, parts.map(([k, v, text]) =>
        el("span", { style: `width:${(100 * v) / total}%;background:${COLORS[k]}`, title: text || `${k} ${pct(v / total)}` }))),
      el("span", { class: "bar-num", text: "" }));
  }
  function single(label, v, max, color, text) {
    return el("div", { class: "bar-row" },
      el("span", { text: label }),
      el("div", { class: "bar-track" }, el("span", { style: `width:${(100 * v) / max}%;background:${color}` })),
      el("span", { class: "bar-num", text }));
  }
  const key = (names) => el("p", { class: "legend" }, names.map((k) =>
    el("span", { style: "margin-right:.9rem" }, el("span", { style: `display:inline-block;width:.7rem;height:.7rem;border-radius:2px;background:${COLORS[k]};margin-right:.3rem` }), k === "left" ? "left without ordering" : k)));

  // ---------------------------------------------------------------------------------------------
  // Figure 1: one question, three views of the same data.
  // ---------------------------------------------------------------------------------------------
  const m1 = document.querySelector("#viz-views");
  if (m1) {
    const v = frame(m1, "Switch or leave? Three views of one question", "computed from the generated Brew Board data");
    const pm = el("div");
    v.root.insertBefore(pm, v.controls);
    let views, segCtl;
    fetch("../data/part4.json").then((r) => r.json()).then((d) => {
      views = [
        () => {
          const s = d.orders_milk_share;
          v.stage.append(
            stacked("Normal hours", ["whole", "oat", "almond"].map((k) => [k, s.normal[k]]), 1),
            stacked("Oat sold out", ["whole", "oat", "almond"].map((k) => [k, s.during[k]]), 1),
            key(["whole", "oat", "almond"]),
            el("p", { html: `Milk lines in afternoon orders. Oat falls from <b>${pct(s.normal.oat)}</b> to <b>${pct(s.during.oat, 1)}</b>. Almond rises from ${pct(s.normal.almond)} to ${pct(s.during.almond)}, whole from ${pct(s.normal.whole)} to ${pct(s.during.whole)}.` }));
          v.foot.innerHTML = "The orders table holds only the people who ordered. Read alone, it says: everyone switched.";
        },
        () => {
          const t = d.dashboard_rate, max = 0.1;
          v.stage.append(
            single("Other days", t.other_days, max, "var(--ink-faint)", pct(t.other_days, 1)),
            single("Sell-out days", t.sellout_days, max, "var(--accent)", pct(t.sellout_days, 1)),
            el("p", { html: `The abandonment tile is <b>lower</b> on days when oat sells out. Of the ${d.leavers.total} sessions that left after they saw oat sold out, the tile counts <b>${d.leavers.counted_by_tile}</b>. ${d.leavers.no_cart} left before they had a cart, so there is no cart to count. The model drops the rest: carts open under 60 seconds are "bounces".` }));
          v.foot.innerHTML = "The tile answers the question it was built for: carts that stalled. It was not built for this one.";
        },
        () => {
          const e = d.events, n = e.sessions_saw_oat_sold_out;
          v.stage.append(
            stacked(`${n} sessions`, [["left", e.left], ["almond", e.almond], ["whole", e.whole]], n),
            key(["left", "almond", "whole"]),
            el("p", { html: `Sessions that saw oat sold out: <b>${e.left} (${pct(e.share.left)}) left</b> without ordering. ${e.almond} (${pct(e.share.almond)}) switched to almond and ${e.whole} (${pct(e.share.whole)}) to whole.` }));
          v.foot.innerHTML = "The session events are app logs. They are not in the warehouse, so BI never sees them.";
        },
      ];
      const show = (i) => { clear(v.stage); views[i](); };
      segCtl = seg(["Orders table", "Dashboard tile", "Session events"], 0, show);
      v.controls.append(segCtl);
      show(0);
      const p = predict(pm, {
        prompt: "When oat sells out at Brew Board, what share of the customers who wanted oat leave without ordering?",
        number: { min: 0, max: 100, step: 1, value: 10 }, unit: "%",
        answer: Math.round(100 * d.events.share.left), tolerance: 0.2,
        explain: "That number is only in the session events. Step through the three views: the orders table and the dashboard both suggest that almost nobody leaves.",
        onLock() { segCtl.querySelectorAll("button")[2].click(); p.reveal(); },
      });
    });
  }

  // ---------------------------------------------------------------------------------------------
  // Figure 2: the same question to an agent, with different access and one sentence.
  // ---------------------------------------------------------------------------------------------
  const m2 = document.querySelector("#viz-agents");
  if (m2) {
    const v = frame(m2, "One question, three agents", "recorded: real claude -p runs, two per setup, not edited");
    const ARMS = [
      ["product", "Morgan's agent", "Works in a folder with the warehouse copy, the inputs and the docs. No code, no logs."],
      ["quiet", "Your agent", "Works in the Brew Board repo. The logs are in <code>../logs</code>, readable with the same tools, but nothing tells the agent that they exist."],
      ["quiet-pointer", "Your agent + one sentence", "Same folder, same tools, same question, plus: <b>“Check the session events in ../logs, not only the orders.”</b>"],
    ];
    const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    function md(text) {
      const out = []; let list = false, table = [];
      const inline = (s) => esc(s).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");
      const flushTable = () => {
        if (!table.length) return;
        const rows = table.filter((r) => !/^\|[\s|:-]+\|$/.test(r)).map((r) => r.slice(1, -1).split("|").map((c) => inline(c.trim())));
        out.push("<table class='mini wrap'>" + rows.map((r, i) => "<tr>" + r.map((c) => (i ? `<td>${c}</td>` : `<th>${c}</th>`)).join("") + "</tr>").join("") + "</table>");
        table = [];
      };
      for (const line of text.split("\n")) {
        if (line.startsWith("|")) { table.push(line.trim()); continue; }
        flushTable();
        if (/^\s*- /.test(line)) { if (!list) { out.push("<ul>"); list = true; } out.push(`<li>${inline(line.replace(/^\s*- /, ""))}</li>`); continue; }
        if (list) { out.push("</ul>"); list = false; }
        if (line.trim()) out.push(`<p>${inline(line)}</p>`);
      }
      flushTable();
      if (list) out.push("</ul>");
      return out.join("");
    }
    // The answer's bold lead if it opens with one, else its first sentence.
    const headline = (a) => { const m = a.match(/^\*\*([^*]+)\*\*/); return m ? m[1] : a.split(/(?<=[.!?])\s/)[0]; };
    fetch("../data/part4-runs.json").then((r) => r.json()).then((d) => {
      let arm = 0, run = 0;
      const show = () => {
        const [name, title, desc] = ARMS[arm];
        const runs = d.runs.filter((r) => r.arm === name);
        const r = runs[run];
        clear(v.stage).append(
          el("p", { class: "legend", html: desc }),
          el("div", { class: "prompt-box" }, el("span", { class: "predict-tag", text: "Asked" }), el("span", { text: r.prompt })),
          el("p", { html: `<b>Run ${run === 0 ? "A" : "B"}:</b> “${esc(headline(r.answer))}” <span class="viz-sub">(other run: “${esc(headline(runs[1 - run].answer))}”)</span>` }),
          el("details", null, el("summary", { text: `What it looked at (${r.calls.length} tool calls)` }),
            el("ol", { class: "calls" }, r.calls.map((c) => el("li", null, el("code", { text: c.what.replace(/^cd [^;&]+(;|&&)\s*/, "").slice(0, 220) }))))),
          el("div", { class: "agent-run", html: md(r.answer) }));
        v.foot.innerHTML = `${title}. Recorded ${d.recorded} with <code>${r.model}</code>. The session events say 35% leave.`;
      };
      v.controls.append(seg(ARMS.map((a) => a[1]), 0, (i) => { arm = i; show(); }), seg(["Run A", "Run B"], 0, (i) => { run = i; show(); }));
      show();
    });
  }
})();
