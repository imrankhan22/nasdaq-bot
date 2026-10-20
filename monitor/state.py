"""Persisted price state.

The state file maps each ticker to its last-seen price and the UTC timestamp
of that observation. It is how the monitor compares "now" against "the last
check" across otherwise-stateless GitHub Actions runs.

Shape:
{
  "updated_at": "2026-10-20T21:30:00+00:00",
  "prices": {
    "AACG": {"price": 0.6575, "ts": "2026-10-20T21:30:00+00:00"},
    ...
  }
}
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"updated_at": None, "prices": {}}
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"updated_at": None, "prices": {}}
    data.setdefault("prices", {})
    return data


def save_state(path: Path, prices: dict[str, dict]) -> None:
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "prices": prices,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
