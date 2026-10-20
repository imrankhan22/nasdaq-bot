"""Entry point: fetch the non-compliant list, compare prices against the last
check, alert on big moves, and persist the new prices.

Run with:  python -m monitor.main
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import config, nasdaq, state, telegram


def _fetch_all_prices(symbols: list[str]) -> dict[str, float]:
    """Fetch current prices for all symbols concurrently."""
    session = nasdaq._make_session()
    prices: dict[str, float] = {}

    def fetch(sym: str):
        return sym, nasdaq.get_price(sym, session=session)

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as pool:
        for sym, price in pool.map(fetch, symbols):
            if price is not None and price > 0:
                prices[sym] = price
    return prices


def _is_alert(pct_change: float) -> bool:
    if config.DIRECTION == "any":
        return abs(pct_change) >= config.THRESHOLD_PCT
    # default: "up"
    return pct_change >= config.THRESHOLD_PCT


def _format_alert(sym: str, old: float, new: float, pct: float, when_old: str | None) -> str:
    arrow = "\U0001F4C8" if pct >= 0 else "\U0001F4C9"  # 📈 / 📉
    sign = "+" if pct >= 0 else ""
    since = f" (last seen {when_old})" if when_old else ""
    return (
        f"{arrow} <b>{sym}</b> moved <b>{sign}{pct:.1f}%</b> since the last check{since}\n"
        f"Price: ${old:.4f} → <b>${new:.4f}</b>\n"
        f"NASDAQ non-compliant list\n"
        f"https://www.nasdaq.com/market-activity/stocks/{sym.lower()}"
    )


def run() -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    print(f"=== NASDAQ non-compliant monitor @ {now_iso} ===")
    print(f"Threshold: {config.THRESHOLD_PCT:.0f}% ({config.DIRECTION})  DRY_RUN={config.DRY_RUN}")

    prev = state.load_state(config.STATE_FILE)
    prev_prices: dict[str, dict] = prev.get("prices", {})

    symbols = nasdaq.get_noncompliant_symbols()
    print(f"Non-compliant tickers: {len(symbols)}")

    current = _fetch_all_prices(symbols)
    print(f"Fetched prices for {len(current)}/{len(symbols)} tickers")

    new_state: dict[str, dict] = {}
    alerts: list[str] = []

    for sym, price in current.items():
        entry = prev_prices.get(sym)
        old_price = entry.get("price") if entry else None

        if old_price and old_price > 0:
            pct = (price - old_price) / old_price * 100.0
            if _is_alert(pct):
                when_old = entry.get("ts") if entry else None
                msg = _format_alert(sym, old_price, price, pct, when_old)
                alerts.append(msg)
                print(f"  ALERT {sym}: {old_price} -> {price} ({pct:+.1f}%)")

        new_state[sym] = {"price": price, "ts": now_iso}

    # Carry forward tickers still on the list but with no price this run, so a
    # transient fetch miss doesn't reset their baseline.
    for sym in symbols:
        if sym not in new_state and sym in prev_prices:
            new_state[sym] = prev_prices[sym]

    print(f"Alerts to send: {len(alerts)}")
    for msg in alerts:
        telegram.send_message(msg)

    state.save_state(config.STATE_FILE, new_state)
    print(f"State saved to {config.STATE_FILE} ({len(new_state)} tickers)")


if __name__ == "__main__":
    run()
