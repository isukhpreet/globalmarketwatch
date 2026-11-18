"""Japan Ministry of Finance JGB reference yields (CSV, no key). Issue #8.

Current-month file (verified 18 Nov 2026):
    Interest Rate (November 2026),,,...,(Unit : %)
    Date,1Y,2Y,3Y,...,10Y,15Y,20Y,25Y,30Y,40Y
    2026/11/2,1.671,1.88,...
The first run also reads the full-history file, whose dates may use Japanese era
notation (e.g. R8.11.4); both formats are parsed.
"""

import csv
import io

from app.collectors.base import get, parse_period, to_float
from app.collectors.macro.catalogue import SeriesSpec
from app.collectors.macro.source import FetchContext, MacroSource
from app.collectors.macro.store import Obs

BASE = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/"
CURRENT = BASE + "jgbcme.csv"
HISTORY = BASE + "historical/jgbcme_all.csv"


def parse_mof_csv(text: str) -> list[dict]:
    lines = text.lstrip("﻿").splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("Date,")), None)
    if start is None:
        return []
    rows = []
    for row in csv.DictReader(io.StringIO("\n".join(lines[start:]))):
        try:
            row["Date"] = parse_period(row["Date"])
        except (ValueError, TypeError, KeyError):
            continue  # footer / blank / note lines
        rows.append(row)
    return rows


class MofSource(MacroSource):
    name = "mof"

    def fetch(self, specs: list[SeriesSpec], ctx: FetchContext) -> dict[str, list[Obs] | Exception]:
        rows: list[dict] = []
        try:
            if not ctx.incremental:
                hist = self.client.get(HISTORY)  # best effort: history file is optional
                if hist.status_code == 200:
                    rows.extend(parse_mof_csv(_decode(hist.content)))
            rows.extend(parse_mof_csv(_decode(get(self.client, CURRENT, None,
                                                  ctx.retry_delay).content)))
        except Exception as e:
            return {s.key: e for s in specs}
        since = ctx.since.isoformat()
        out: dict[str, list[Obs] | Exception] = {}
        for spec in specs:
            if rows and spec.source_id not in rows[-1]:
                out[spec.key] = KeyError(f"Column {spec.source_id!r} not in MoF CSV")
                continue
            series = {r["Date"]: to_float(r.get(spec.source_id)) for r in rows
                      if r["Date"] >= since}
            out[spec.key] = sorted(series.items())
        return out


def _decode(b: bytes) -> str:
    for enc in ("utf-8-sig", "cp932"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")
