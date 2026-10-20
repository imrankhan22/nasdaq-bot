"""NASDAQ API client.

Two things are needed from NASDAQ:

1. The list of non-compliant (a.k.a. "deficient") company tickers, which
   backs https://www.nasdaq.com/market-activity/stocks/non-compliant-company-list
2. The current price for each of those tickers.

Both come from the undocumented but public api.nasdaq.com JSON endpoints that
the website itself calls. They require browser-like headers or they return an
empty body.
"""
from __future__ import annotations

import time
from typing import Optional

import requests

from . import config

API_BASE = "https://api.nasdaq.com/api"

LIST_URL = f"{API_BASE}/quote/list-type-extended/listing"
LIST_PARAMS = {"queryString": "deficient"}

# NASDAQ rejects requests without these headers.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def _get_json(session: requests.Session, url: str, params: Optional[dict] = None) -> Optional[dict]:
    """GET a URL and return parsed JSON, retrying transient failures."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            resp = session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
            if resp.status_code == 200 and resp.content:
                return resp.json()
            last_exc = RuntimeError(f"HTTP {resp.status_code}")
        except (requests.RequestException, ValueError) as exc:  # network / bad JSON
            last_exc = exc
        if attempt < config.MAX_RETRIES:
            time.sleep(0.5 * attempt)  # simple backoff
    print(f"  ! request failed for {url}: {last_exc}")
    return None


def get_noncompliant_symbols(session: Optional[requests.Session] = None) -> list[str]:
    """Return the sorted list of unique tickers on the non-compliant list."""
    session = session or _make_session()
    data = _get_json(session, LIST_URL, LIST_PARAMS)
    if not data:
        raise RuntimeError("Could not fetch the non-compliant company list.")

    rows = (
        (data.get("data") or {})
        .get("noncomplaintCompanyList", {})  # NASDAQ's own (mis)spelling
        .get("rows")
        or []
    )

    symbols: set[str] = set()
    for row in rows:
        for company in row.get("companies", []) or []:
            for issue in company.get("AffectedIssues", []) or []:
                sym = str(issue).strip().upper()
                if sym:
                    symbols.add(sym)
    return sorted(symbols)


def _parse_price(raw: Optional[str]) -> Optional[float]:
    """Turn a value like '$0.6575' or '1,234.5' into a float."""
    if not raw:
        return None
    cleaned = str(raw).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def get_price(symbol: str, session: Optional[requests.Session] = None) -> Optional[float]:
    """Return the current last-sale price for a ticker, or None if unavailable."""
    session = session or _make_session()
    url = f"{API_BASE}/quote/{symbol}/info"
    data = _get_json(session, url, {"assetclass": "stocks"})
    if not data:
        return None
    primary = (data.get("data") or {}).get("primaryData") or {}
    return _parse_price(primary.get("lastSalePrice"))
