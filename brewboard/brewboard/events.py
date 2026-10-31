"""Session events from the customer page.

Written as JSON lines, one file per day, and shipped to log storage with the app logs.
"""
import json
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs" / "session_events"


def emit(ts, store, session, customer, event, **fields):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rec = {"ts": ts, "store": store, "session": session, "customer": customer, "event": event, **fields}
    with open(LOG_DIR / f"{ts[:10]}.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
