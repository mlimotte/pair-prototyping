"""Build the site and serve it, with the API for part 2's live example.

    python serve.py build          # site/ + kit/ → _site/
    python serve.py serve [port]   # build, then serve on http://localhost:8765/

The API runs `claude -p` with no tools and no user settings, in a temp directory, so it uses the
learner's own Claude Code login and no API key.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE, KIT, OUT = ROOT / "site", ROOT / "kit", ROOT / "_site"
PORT = 8765
MODEL = os.environ.get("BACKLOG_MODEL", "sonnet")

PROMPTS = {
    "plain": "You are a product assistant. Turn the request into a feature spec of about 250 words: "
             "problem, users, solution, requirements, success metrics. Plain text with short headings. No preamble.",
    "guided": "You write feature specs. Use only what the request says. Do not guess. Wherever the spec needs a "
              "fact or a decision that the request does not give, write [NEEDS CLARIFICATION: one specific question] "
              "instead. Sections: Problem, Users, Requirements (each one testable), Out of scope, Open questions. "
              "Plain text with short headings. No preamble.",
    "decide": "You write feature specs. State as fact only what the request says. For each fact or decision the "
              "spec needs that the request does not give, sort it by risk and confidence. Low risk, easy to change "
              "later, or you are highly confident: decide it, and write [DEFAULT: the decision. One-line reason.] "
              "Moderate risk: recommend, and write [RECOMMEND: the option. Reason. Alternative: the other option.] "
              "High risk, hard to reverse, or it needs facts only the team has (its data, its system, its business): "
              "ask, and write [NEEDS CLARIFICATION: one specific question]. Never state an invented fact or number as "
              "known. Sections: Problem, Users, Requirements (each one testable), Out of scope, Open questions. "
              "Plain text with short headings. No preamble.",
    "attribute": 'You compare a SOURCE with an OUTPUT. Split the OUTPUT into sentences, keeping the exact text; a '
                 'heading or list item is its own sentence, and a bracketed marker is one sentence. Label each one: '
                 '"question" if it is a question or a [NEEDS CLARIFICATION] marker; "default" if it is a [DEFAULT] '
                 'marker; "recommend" if it is a [RECOMMEND] marker; "prompt" if everything it asserts is stated in '
                 'the SOURCE or follows directly from it (a heading counts as "prompt"); otherwise "invented" (it adds '
                 'a fact, number, name, requirement or decision that the SOURCE does not give, without a marker). '
                 'Output only JSON, no code fence: [{"s": "...", "label": "prompt|invented|question|default|recommend"}]',
}


# ------------------------------------------------------------------------------------------------
# claude -p
# ------------------------------------------------------------------------------------------------
def claude(system, user, timeout=240):
    """Run one isolated, tool-less `claude -p` call. Return (text, model id)."""
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["claude", "-p", "--setting-sources", "", "--strict-mcp-config", "--tools", "",
                            "--no-session-persistence", "--output-format", "json", "--model", MODEL,
                            "--system-prompt", system, user],
                           cwd=tmp, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-500:] or f"claude exited {r.returncode}")
    d = json.loads(r.stdout)
    if d.get("is_error"):
        raise RuntimeError(d.get("result") or "claude returned an error")
    return d["result"].strip(), next(iter(d.get("modelUsage") or {MODEL: 0}))


def expand(prompt, mode):
    return claude(PROMPTS[mode], prompt)


def attribute(prompt, output):
    raw, model = claude(PROMPTS["attribute"], f"SOURCE:\n{prompt}\n\nOUTPUT:\n{output}")
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    return json.loads(raw[raw.index("["):raw.rindex("]") + 1]), model


# ------------------------------------------------------------------------------------------------
# build
# ------------------------------------------------------------------------------------------------
def fill(template, **kw):
    for k, v in kw.items():
        template = template.replace("{{" + k + "}}", str(v))
    return template


def build():
    c = json.loads((ROOT / "learning.json").read_text())
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(KIT / "assets", OUT / "assets")
    for sub in ("cards", "wild", "viz"):
        if (SITE / sub).exists():
            shutil.copytree(SITE / sub, OUT / "assets" / sub, dirs_exist_ok=True)
    if (SITE / "static").exists():
        shutil.copytree(SITE / "static", OUT, dirs_exist_ok=True)
    have = lambda sub: sorted(f.stem for f in (SITE / sub).glob("[0-9][0-9].js"))
    if not (OUT / "assets/wild/sources.js").exists():
        (OUT / "assets/wild").mkdir(parents=True, exist_ok=True)
        (OUT / "assets/wild/sources.js").write_text("window.SOURCE_BLURBS = {};\n")
    (OUT / "assets/site.js").write_text("window.SITE = " + json.dumps(
        {"title": c["title"], "parts": [dict(p, wip=not (SITE / "posts" / f"{i:02d}-{p['slug']}.html").exists())
                                        for i, p in enumerate(c["parts"], 1)],
         "cards": have("cards"), "wild": have("wild")}, indent=1) + ";\n")
    common = dict(TITLE=html.escape(c["title"]), HEADLINE=html.escape(c["headline"]),
                  TAGLINE=html.escape(c["tagline"]), PART_COUNT=len(c["parts"]))
    pages = KIT / "pages"
    (OUT / "index.html").write_text(fill((pages / "index.html").read_text(), INTRO=(SITE / "intro.html").read_text(), **common))
    for name in ("review", "wild"):
        (OUT / f"{name}.html").write_text(fill((pages / f"{name}.html").read_text(), **common))
    (OUT / "posts").mkdir()
    for i, p in enumerate(c["parts"], 1):
        name = f"{i:02d}-{p['slug']}"
        src = SITE / "posts" / f"{name}.html"
        content = src.read_text() if src.exists() else (
            f'  <h1>{html.escape(p["title"])}</h1>\n  <p class="dek">{html.escape(p["desc"])}</p>\n'
            '  <p class="wip-banner">Work in progress: this part is not written yet.</p>\n')
        head = f'<script src="../assets/viz/{name}.js" defer></script>' if (SITE / "viz" / f"{name}.js").exists() else ""
        (OUT / "posts" / f"{name}.html").write_text(fill((pages / "post.html").read_text(), CONTENT=content,
            HEAD_EXTRA=head, PART_N=i, PART_TITLE=html.escape(p["title"]), **common))
    print(f"built {OUT.relative_to(ROOT)} ({len(c['parts'])} parts)")


# ------------------------------------------------------------------------------------------------
# serve
# ------------------------------------------------------------------------------------------------
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(OUT), **kw)

    def json(self, status, obj):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/health":
            return self.json(200, {"claude": bool(shutil.which("claude")), "model": MODEL})
        super().do_GET()

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path == "/api/expand":
                if body.get("mode") not in ("plain", "guided", "decide"):
                    return self.json(400, {"error": "mode must be plain, guided or decide"})
                output, model = expand(body["prompt"], body["mode"])
                return self.json(200, {"output": output, "model": model})
            if self.path == "/api/attribute":
                sentences, model = attribute(body["prompt"], body["output"])
                return self.json(200, {"sentences": sentences, "model": model})
            self.json(404, {"error": "not found"})
        except Exception as e:  # report to the page; the page falls back to recorded runs
            self.json(500, {"error": str(e)})


def serve(port=PORT):
    build()
    print(f"serving http://localhost:{port}/")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "serve"
    if cmd == "build":
        build()
    elif cmd == "serve":
        serve(int(sys.argv[2]) if len(sys.argv) > 2 else PORT)
    else:
        sys.exit(__doc__)
