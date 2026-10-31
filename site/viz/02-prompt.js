(function () {
  const { el, clear, frame, seg, predict } = EE;
  const LABEL = { prompt: "from your prompt", invented: "invented", question: "question", default: "agent decided (labeled)", recommend: "agent recommends" };
  const MODE_NAME = { guided: "With guidelines", decide: "With decision rules" };

  function sentences(list) {
    return el("div", { class: "spec-out" }, list.map((x) =>
      el("span", { class: "sent " + x.label, title: LABEL[x.label] || x.label, text: x.s + " " })));
  }
  function counts(list) {
    const c = { prompt: 0, invented: 0, question: 0, default: 0, recommend: 0 };
    list.forEach((x) => { c[x.label] = (c[x.label] || 0) + 1; });
    return c;
  }
  function stats(list) {
    const c = counts(list);
    const stat = (k, label) => el("div", { class: "stat" }, el("b", { class: "k-" + k, text: c[k] }), el("span", { text: label }));
    return el("div", { class: "stats-row" }, stat("prompt", "from your prompt"), stat("invented", "invented, unlabeled"),
      c.default ? stat("default", "labeled defaults") : null, c.recommend ? stat("recommend", "recommendations") : null,
      stat("question", "questions"));
  }
  const legend = (list) => {
    const c = counts(list || []);
    return el("p", { class: "legend" }, ["prompt", "invented", "default", "recommend", "question"]
      .filter((k) => !list || c[k] || k === "prompt" || k === "invented")
      .map((k) => [el("span", { class: "sent " + k, text: LABEL[k] }), " "]));
  };

  function loadRuns() {
    return fetch("../data/part2-runs.json").then((r) => r.json());
  }

  // ---------------------------------------------------------------------------------------------
  // Figure 1: the same prompt, run three times, then with guidelines.
  // ---------------------------------------------------------------------------------------------
  const m1 = document.querySelector("#viz-runs");
  if (m1) {
    const v = frame(m1, "One prompt, five runs", "recorded: real claude -p output, labeled by a second pass");
    const pm = el("div");
    v.root.insertBefore(pm, v.controls);
    let show = () => {};
    const p = predict(pm, {
      prompt: "You run the same two-sentence prompt three times. Which sentences stay the same from run to run?",
      choices: ["The invented details: numbers, rules, lists", "The sentences that come from the prompt", "Both", "Neither: everything changes"],
      answer: 1,
      explain: "Step through runs 1 to 3. The green sentences say the same thing each time. The amber ones change: each run invents different targets, rules and users. Look at the success metrics.",
      onLock() { show(0); p.reveal(); },
    });
    loadRuns().then((d) => {
      const names = d.runs.map((r, i) => MODE_NAME[r.mode] || `Run ${i + 1}`);
      show = (i) => {
        const r = d.runs[i];
        clear(v.stage).append(
          el("div", { class: "prompt-box" }, el("span", { class: "predict-tag", text: { guided: "Prompt + do not guess", decide: "Prompt + decision rules" }[r.mode] || "Prompt" }), el("span", { text: d.prompt })),
          stats(r.sentences), legend(r.sentences), sentences(r.sentences));
        v.foot.innerHTML = {
          guided: "Same prompt, plus one rule: <b>mark each unknown as a question, do not guess</b>. The output is the prompt and a list of questions.",
          decide: "Same prompt, plus rules by risk: <b>decide</b> what is low risk (labeled), <b>recommend</b> on moderate risk, <b>ask</b> where the risk is high or the facts are the team's. Amber: decisions it made without a label.",
        }[r.mode] || `Run ${i + 1} of the same prompt. Recorded ${d.recorded} with <code>${r.model}</code>.`;
      };
      v.controls.append(seg(names, 0, show));
      v.controls.append(el("button", { text: "Invented numbers, by run", onclick: () => numbers(d) }));
      show(0);
    });

    function numbers(d) {
      const plain = d.runs.filter((r) => r.mode === "plain");
      const rows = plain.map((r, i) => [`Run ${i + 1}`, r.sentences.filter((x) => x.label === "invented" && /\d+\s*%/.test(x.s)).map((x) => x.s.replace(/^[-\d.\s]+/, "")).join(" · ")]);
      clear(v.stage).append(el("table", { class: "mini wrap" },
        el("thead", null, el("tr", null, el("th", { text: "" }), el("th", { text: "Invented sentences with a percentage" }))),
        el("tbody", null, rows.map(([a, b]) => el("tr", null, el("td", { text: a }), el("td", { text: b }))))));
      v.foot.textContent = "Each run sets different targets for the same feature. None of them came from anyone who knows Brew Board.";
    }
  }

  // ---------------------------------------------------------------------------------------------
  // Figure 2: does any invented sentence record a decision?
  // ---------------------------------------------------------------------------------------------
  const m2 = document.querySelector("#viz-decisions");
  if (m2) {
    predict(m2, {
      prompt: "Run 1 has 19 invented sentences. How many of them record a decision that someone at Brew Board made?",
      choices: ["All 19", "About half", "A few", "None"],
      answer: 3,
      explain: "Nobody at Brew Board saw the run before it was written. A sentence like “acceptance rate of at least 60%” has the form of a decision, but nobody decided it. Run 2 says 50%.",
    });
  }

  // ---------------------------------------------------------------------------------------------
  // Figure 3: live, with the learner's own Claude Code (needs `python serve.py`).
  // ---------------------------------------------------------------------------------------------
  const m3 = document.querySelector("#viz-live");
  if (m3) {
    const v = frame(m3, "Try it", "your prompt, your Claude Code");
    const ta = el("textarea", { class: "live-prompt", rows: 4 });
    const status = el("span", { class: "viz-sub" });
    const btnPlain = el("button", { class: "primary", text: "Run", disabled: true });
    const btnGuided = el("button", { text: "Run with guidelines", disabled: true });
    const btnDecide = el("button", { text: "Run with decision rules", disabled: true });
    const buttons = [btnPlain, btnGuided, btnDecide];
    v.controls.append(...buttons, status);
    v.root.insertBefore(ta, v.controls);
    loadRuns().then((d) => { ta.value = d.prompt; });
    fetch("/api/health").then((r) => (r.ok ? r.json() : null)).catch(() => null).then((h) => {
      if (!h) v.foot.innerHTML = "Live runs work only in a local clone of the series repo: run <code>python serve.py</code>, then open <code>http://localhost:8765</code>. You need that only for the exercises. The figures above show recorded runs.";
      if (!h || !h.claude) { status.textContent = h ? "claude is not on the PATH" : "offline: showing recorded runs only"; return; }
      buttons.forEach((b) => { b.disabled = false; });
      status.textContent = `ready (model: ${h.model})`;
    });

    async function run(mode) {
      buttons.forEach((b) => { b.disabled = true; });
      const t0 = Date.now();
      const tick = setInterval(() => { status.textContent = `running… ${Math.round((Date.now() - t0) / 1000)} s`; }, 500);
      try {
        const post = (url, body) => fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) })
          .then((r) => r.json()).then((j) => { if (j.error) throw new Error(j.error); return j; });
        const e = await post("/api/expand", { prompt: ta.value, mode });
        status.textContent = "labeling…";
        const a = await post("/api/attribute", { prompt: ta.value, output: e.output });
        clear(v.stage).append(stats(a.sentences), legend(a.sentences), sentences(a.sentences));
        v.foot.innerHTML = `${MODE_NAME[mode] || "Plain"} · <code>${e.model}</code> · ${Math.round((Date.now() - t0) / 1000)} s. Run it again and compare.`;
      } catch (err) {
        v.foot.textContent = "The run failed: " + err.message;
      } finally {
        clearInterval(tick);
        status.textContent = "";
        buttons.forEach((b) => { b.disabled = false; });
      }
    }
    btnPlain.addEventListener("click", () => run("plain"));
    btnGuided.addEventListener("click", () => run("guided"));
    btnDecide.addEventListener("click", () => run("decide"));
  }
})();
