"""Record real part 4 runs: the same question, the same access, with and without one sentence.

    python tools/record_part4.py <starter dir> [runs per arm] [arm,arm...] > site/static/data/part4-runs.json

Each run is `claude -p` with read-only tools. Arms differ in working folder, whether ../logs is announced
with --add-dir, and the engineer's pointer (see ARMS). Paths are written as <starter>. Never edit the output by hand.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

QUESTION = ("Morgan, the product owner, asks: when oat milk sells out, do customers switch to another milk, "
            "or do they leave? Answer from the data you can find, with numbers. At most 200 words. "
            "End with the sources you used.")
POINTER = "Check the session events, not only the orders."
POINTER_PATH = "Check the session events in ../logs, not only the orders."
# arm -> (working dir under the starter, announce ../logs with --add-dir, pointer sentence)
ARMS = {
    "none":          ("brewboard", True, None),
    "pointer":       ("brewboard", True, POINTER),
    "product":       ("product", False, None),
    "quiet":         ("brewboard", False, None),
    "quiet-pointer": ("brewboard", False, POINTER_PATH),
}
TOOLS = ["Read", "Grep", "Glob", "Bash(sqlite3:*)", "Bash(python3:*)", "Bash(ls:*)", "Bash(head:*)", "Bash(wc:*)",
         "Bash(cat:*)", "Bash(grep:*)", "Bash(find:*)", "Bash(jq:*)", "Bash(git log:*)", "Bash(git branch:*)",
         "Bash(git show:*)"]


def run(starter, arm):
    cwd, announce, pointer = ARMS[arm]
    prompt = QUESTION + (" " + pointer if pointer else "")
    r = subprocess.run(["claude", "-p", *(["--add-dir", "../logs"] if announce else []), "--strict-mcp-config",
                        "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--model", "sonnet",
                        "--allowedTools", *TOOLS, "--", prompt],
                       cwd=Path(starter) / cwd, capture_output=True, text=True, timeout=900)
    calls, result, model = [], "", None
    for line in r.stdout.splitlines():
        try:
            m = json.loads(line)
        except json.JSONDecodeError:
            continue
        if m.get("type") == "assistant":
            model = model or m["message"].get("model")
            for b in m["message"].get("content", []):
                if b.get("type") == "tool_use":
                    i = b["input"]
                    calls.append({"tool": b["name"], "what": i.get("command") or i.get("file_path") or i.get("pattern") or json.dumps(i)[:200]})
        elif m.get("type") == "result":
            result = m.get("result", "")
    return {"arm": arm, "cwd": cwd, "announced_logs": announce, "prompt": prompt, "model": model, "calls": calls, "answer": result.strip()}


if __name__ == "__main__":
    starter, n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1
    names = sys.argv[3].split(",") if len(sys.argv) > 3 else list(ARMS)
    arms = [a for a in names for _ in range(n)]
    with ThreadPoolExecutor(len(arms)) as pool:
        runs = list(pool.map(lambda a: run(starter, a), arms))
    text = json.dumps({"recorded": date.today().isoformat(), "question": QUESTION, "runs": runs}, indent=1)
    print(text.replace(str(Path(starter).resolve()), "<starter>"))
