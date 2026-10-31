"""Build a starter folder for one part's exercise.

    python starters/make_starter.py 04 ~/backlog-series/part04

Layout of the result:
    brewboard/   a git repo with history (and the abandoned `substitutions` branch), data/, inputs/
    logs/        session events and counter logs: log storage, outside the repo
    product/     what a product person's agent sees: the warehouse copy, inputs and docs (no code, no logs)
    EXERCISE.md  what to do
    answer.md    where the learner writes
    grade/       the grader skill and the reference answer (run Claude Code here to grade)
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TEMPLATE = ROOT / "brewboard"

STOCK_NO_CACHE = '''"""Sold-out milks. The barista marks a milk out; customers cannot pick it."""
from . import db


def sold_out(conn, store_id, now=None):
    """Return the set of milks sold out at a store."""
    return _read(conn, store_id)


def _read(conn, store_id):
    rows = conn.execute(
        "select milk, sold_out from stock_events where store_id = ? order by at", (store_id,)).fetchall()
    out = set()
    for r in rows:
        (out.add if r["sold_out"] else out.discard)(r["milk"])
    return out


def toggle(conn, store_id, milk, at):
    """Barista action: flip a milk between sold out and available."""
    now_out = milk not in _read(conn, store_id)
    conn.execute("insert into stock_events values (?, ?, ?, ?)", (store_id, milk, at, int(now_out)))
    conn.commit()
    return now_out
'''

SUBSTITUTE = '''"""Suggest a substitute when the chosen milk is sold out. WIP: see NOTES.md."""
from .menu import MENU

PREFERENCE = {"oat": ["almond", "whole"], "almond": ["oat", "whole"], "whole": ["oat", "almond"]}


def suggest(drink, milk, sold_out):
    """Return the first milk the drink offers that is not sold out, or None."""
    for alt in PREFERENCE.get(milk, []):
        if alt in MENU[drink]["milks"] and alt not in sold_out:
            return alt
    return None


def substituted_line(line, sold_out):
    """Return the line with the milk swapped, recording what the customer asked for."""
    alt = suggest(line["drink"], line["milk"], sold_out)
    # TODO: the POS rejects this: requested_milk is not in the v3 line contract
    return {**line, "milk": alt, "requested_milk": line["milk"]}
'''

NOTES = '''# substitutions: paused

Goal: when a customer picks a sold-out milk, suggest one that is in stock, and at the counter swap the milk on the line instead of refunding.

Paused (Jo, 2026-06-19):
- The POS v3 contract rejects any field we add to a line (`additionalProperties: false`), so we cannot send `requested_milk`. Without it, inventory still counts the wrong milk.
- Swapping the milk on a placed line is the same change that caused the March double charge (docs/postmortems/2026-03-14-sold-out-double-charge.md).
- The vendor's v4 contract has line replacement. Not scheduled.

What would unblock: suggest BEFORE the line is placed (no change to a placed line, no new field). Did not get to try it.
'''


def git(repo, *args, date=None):
    env = {**os.environ, "GIT_AUTHOR_NAME": "Brew Board", "GIT_AUTHOR_EMAIL": "dev@brewboard.example",
           "GIT_COMMITTER_NAME": "Brew Board", "GIT_COMMITTER_EMAIL": "dev@brewboard.example"}
    if date:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env, capture_output=True)


def commit(repo, msg, date, author=None):
    git(repo, "add", "-A")
    args = ["commit", "-q", "-m", msg] + (["--author", author] if author else [])
    git(repo, *args, date=date)


def build_repo(repo):
    shutil.copytree(TEMPLATE, repo, ignore=shutil.ignore_patterns("__pycache__", "brewboard.db", "data", "inputs"))
    held = {p: (repo / p).read_text() for p in ("brewboard/stock.py",)}
    held_dirs = {}
    for d in ("warehouse", "docs/postmortems"):
        held_dirs[d] = repo / ".." / f".held-{d.replace('/', '-')}"
        shutil.move(repo / d, held_dirs[d])
    (repo / "brewboard/stock.py").write_text(STOCK_NO_CACHE)
    (repo / ".gitignore").write_text("__pycache__/\nbrewboard.db\ndata/\n")
    git(repo, "init", "-q", "-b", "main")
    commit(repo, "Brew Board: menu, carts, orders, the board", "2026-01-12T10:00:00")

    shutil.move(held_dirs["docs/postmortems"], repo / "docs/postmortems")
    commit(repo, "Postmortem: double charges after the counter line edit (edit removed)", "2026-03-16T15:20:00")

    shutil.move(held_dirs["warehouse"], repo / "warehouse")
    commit(repo, "Warehouse: nightly load and the abandonment tile", "2026-04-08T11:05:00")

    (repo / "brewboard/stock.py").write_text(held["brewboard/stock.py"])
    commit(repo, "Cache stock reads; the POS was slow at peak", "2026-05-21T09:40:00")

    git(repo, "checkout", "-q", "-b", "substitutions")
    (repo / "brewboard/substitute.py").write_text(SUBSTITUTE)
    commit(repo, "WIP: suggest a substitute milk", "2026-06-12T16:10:00", "Jo <jo@brewboard.example>")
    (repo / "NOTES.md").write_text(NOTES)
    commit(repo, "Pause substitutions: POS contract, see NOTES.md", "2026-06-19T17:30:00", "Jo <jo@brewboard.example>")
    git(repo, "checkout", "-q", "main")


def main():
    part, dest = sys.argv[1], Path(sys.argv[2]).expanduser().resolve()
    src = HERE / f"part{part}"
    if not src.exists():
        sys.exit(f"no starter for part {part}")
    if dest.exists():
        sys.exit(f"{dest} exists; remove it first")
    dest.mkdir(parents=True)
    repo = dest / "brewboard"
    build_repo(repo)
    subprocess.run([sys.executable, str(ROOT / "datagen/generate.py"), "--repo", str(repo), "--logs", str(dest / "logs")],
                   check=True, capture_output=True)
    git(repo, "add", "inputs")
    git(repo, "commit", "-q", "-m", "Inputs from Morgan for the sell-out discovery", date="2026-09-29T09:00:00")
    for sub in ("data", "inputs", "docs"):
        shutil.copytree(repo / sub, dest / "product" / sub)
    shutil.copy(repo / "warehouse/README.md", dest / "product/data/README.md")
    shutil.copy(src / "EXERCISE.md", dest / "EXERCISE.md")
    (dest / "answer.md").write_text("# My answer\n\n")
    skill = dest / "grade/.claude/skills/grade"
    skill.mkdir(parents=True)
    shutil.copy(HERE / "grader-skill.md", skill / "SKILL.md")
    shutil.copy(src / "rubric.md", dest / "grade/rubric.md")
    shutil.copy(src / "reference.md", dest / "grade/reference.md")
    print(f"starter for part {part}: {dest}")
    print(f"  read {dest / 'EXERCISE.md'}")


if __name__ == "__main__":
    main()
