"""Configuration, read from environment variables.

Secrets (Telegram) come from GitHub Actions secrets at runtime; everything
else has a sensible default so the app runs with zero configuration.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Telegram (required to actually send alerts) -------------------------
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# --- Alert logic ---------------------------------------------------------
# Percentage move (since the previous check) that triggers an alert.
THRESHOLD_PCT: float = float(os.getenv("THRESHOLD_PCT", "25"))

# "up"  -> alert only when price rises by >= THRESHOLD_PCT
# "any" -> alert on a move of >= THRESHOLD_PCT in either direction
DIRECTION: str = os.getenv("DIRECTION", "up").strip().lower()

# --- State ---------------------------------------------------------------
# File that remembers each ticker's last-seen price between runs. It is
# committed back to the repo by the GitHub Actions workflow.
STATE_FILE: Path = Path(os.getenv("STATE_FILE", "state.json"))

# --- HTTP / performance --------------------------------------------------
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "20"))
MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "8"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

# --- Behaviour flags -----------------------------------------------------
# When true, do everything except actually sending the Telegram message.
DRY_RUN: bool = os.getenv("DRY_RUN", "").strip().lower() in {"1", "true", "yes"}


def telegram_configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
