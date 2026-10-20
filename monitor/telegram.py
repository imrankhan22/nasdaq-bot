"""Minimal Telegram Bot API sender."""
from __future__ import annotations

import requests

from . import config


def send_message(text: str) -> bool:
    """Send a message to the configured chat. Returns True on success."""
    if config.DRY_RUN:
        print("  [DRY_RUN] would send Telegram message:")
        print("  " + text.replace("\n", "\n  "))
        return True

    if not config.telegram_configured():
        print("  ! Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing).")
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, data=payload, timeout=config.REQUEST_TIMEOUT)
        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        print(f"  ! Telegram API error {resp.status_code}: {resp.text[:200]}")
    except (requests.RequestException, ValueError) as exc:
        print(f"  ! Telegram send failed: {exc}")
    return False
