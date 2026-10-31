"""Record real part 2 runs as page data: the same prompt, three plain runs and one guided run.

    python tools/record_part2.py > site/static/data/part2-runs.json
    python tools/record_part2.py decide          # record one more mode and append it to the file

Each run is expanded by one `claude -p` call and labeled by a second. Never edit the output by hand.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import serve  # noqa: E402

PROMPT = ("When oat milk sells out, customers who wanted oat either switch to another milk or leave. "
          "When the milk a customer picks is sold out, suggest a substitute.")
RUNS = ["plain", "plain", "plain", "guided", "decide"]
DATA = Path(__file__).resolve().parent.parent / "site/static/data/part2-runs.json"


def one(mode):
    output, model = serve.expand(PROMPT, mode)
    sentences, label_model = serve.attribute(PROMPT, output)
    return {"mode": mode, "model": model, "label_model": label_model, "output": output, "sentences": sentences}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        d = json.loads(DATA.read_text())
        for mode in sys.argv[1:]:
            d["runs"].append({**one(mode), "recorded": date.today().isoformat()})
        DATA.write_text(json.dumps(d, indent=1) + "\n")
    else:
        with ThreadPoolExecutor(len(RUNS)) as pool:
            runs = list(pool.map(one, RUNS))
        print(json.dumps({"recorded": date.today().isoformat(), "prompt": PROMPT, "runs": runs}, indent=1))
