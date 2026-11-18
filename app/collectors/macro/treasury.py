"""US Treasury daily par yield curve (CSV, no key). Issue #5.

Format (verified 18 Nov 2026):
    Date,"1 Mo","1.5 Month","2 Mo","3 Mo",...,"30 Yr"
    11/17/2026,4.09,4.24,...
"""

import csv
import io
from datetime import date

from app.collectors.base import get, parse_period, to_float
from app.collectors.macro.catalogue import SeriesSpec
from app.collectors.macro.source import FetchContext, MacroSource
from app.collectors.macro.store import Obs

URL = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
       "daily-treasury-rates.csv/{year}/all")


class TreasurySource(MacroSource):
    name = "treasury"

    def fetch(self, specs: list[SeriesSpec], ctx: FetchContext) -> dict[str, list[Obs] | Exception]:
        rows: list[dict] = []
        try:
            for year in range(ctx.since.year, date.today().year + 1):
                text = get(self.client, URL.format(year=year), {
                    "type": "daily_treasury_yield_curve",
                    "field_tdr_date_value": str(year),
                    "page": "",
                    "_format": "csv",
                }, ctx.retry_delay).text
                rows.extend(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
        except Exception as e:
            return {s.key: e for s in specs}
        out: dict[str, list[Obs] | Exception] = {}
        for spec in specs:
            if rows and spec.source_id not in rows[0]:
                out[spec.key] = KeyError(f"Column {spec.source_id!r} not in Treasury CSV")
                continue
            out[spec.key] = [
                (parse_period(r["Date"]), to_float(r.get(spec.source_id))) for r in rows
            ]
        return out
