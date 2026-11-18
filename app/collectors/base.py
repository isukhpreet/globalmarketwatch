"""Shared building blocks for all collectors (issue #2).

- `make_client()`  — one HTTP client config (timeouts, polite User-Agent)
- `retry()`        — retries with exponential backoff for transient failures
- `parse_period()` — turns every date/period format the sources use into ISO YYYY-MM-DD
"""

import re
import time
from collections.abc import Callable
from datetime import date, datetime

import httpx

USER_AGENT = "Mozilla/5.0 (compatible; GlobalMarketWatch; personal non-commercial use)"


class CollectorError(RuntimeError):
    """A source returned something we can't use (bad status, error payload, unknown format)."""


def make_client(timeout: float = 30.0) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        follow_redirects=True,
    )


def retry[T](fn: Callable[[], T], attempts: int = 3, base_delay: float = 2.0) -> T:
    """Call fn; on network errors or 5xx/429 responses retry with 2s, 8s… backoff."""
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except httpx.HTTPStatusError as e:
            last = e
            if e.response.status_code not in (429, 500, 502, 503, 504):
                raise
        except (httpx.TransportError, httpx.TimeoutException) as e:
            last = e
        if i < attempts - 1 and base_delay > 0:
            time.sleep(base_delay * (4**i))
    assert last is not None
    raise last


def get(client: httpx.Client, url: str, params: dict | None = None,
        retry_delay: float = 2.0) -> httpx.Response:
    def _do() -> httpx.Response:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r
    return retry(_do, base_delay=retry_delay)


_MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
_ERAS = {"R": 2018, "H": 1988, "S": 1925}  # Reiwa, Heisei, Showa


def parse_period(s: str | int) -> str:
    """Normalise a date or period to ISO 'YYYY-MM-DD' (periods map to their first day).

    Handles: 2026-11-17, 2026-11, 2026-Q3, 2026Q3, 20261117, 202611, 2026,
    11/17/2026 (US), 2026/11/4 (JP), R8.11.4 (JP era), '2026 JAN', '2026 Q1',
    '01 Oct 2026' (BoE).
    """
    s = str(s).strip()
    if m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s):
        return s
    if m := re.fullmatch(r"(\d{4})-(\d{2})", s):
        return f"{m[1]}-{m[2]}-01"
    if m := re.fullmatch(r"(\d{4})[- ]?Q([1-4])", s):
        return f"{m[1]}-{(int(m[2]) - 1) * 3 + 1:02d}-01"
    if m := re.fullmatch(r"(\d{4})(\d{2})(\d{2})", s):
        return f"{m[1]}-{m[2]}-{m[3]}"
    if m := re.fullmatch(r"(\d{4})(\d{2})", s):
        return f"{m[1]}-{m[2]}-01"
    if m := re.fullmatch(r"(\d{4})", s):
        return f"{m[1]}-01-01"
    if m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s):
        return date(int(m[3]), int(m[1]), int(m[2])).isoformat()
    if m := re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", s):
        return date(int(m[1]), int(m[2]), int(m[3])).isoformat()
    if m := re.fullmatch(r"([RHS])(\d{1,2})\.(\d{1,2})\.(\d{1,2})", s):
        return date(_ERAS[m[1]] + int(m[2]), int(m[3]), int(m[4])).isoformat()
    if m := re.fullmatch(r"(\d{4}) ([A-Z]{3})", s.upper()):
        return f"{m[1]}-{_MONTHS[m[2]]:02d}-01"
    if m := re.fullmatch(r"\d{1,2} [A-Za-z]{3} \d{4}", s):
        return datetime.strptime(s, "%d %b %Y").date().isoformat()
    raise ValueError(f"Unrecognised date/period: {s!r}")


def to_float(v) -> float | None:
    """Parse a numeric cell; blanks, '.', 'NA', '-' and similar become None."""
    if v is None:
        return None
    if isinstance(v, int | float):
        return float(v)
    s = str(v).strip().replace(",", "")
    if s in ("", ".", "-", "NA", "N/A", "NaN", "null", "ND"):
        return None
    try:
        return float(s)
    except ValueError:
        return None
