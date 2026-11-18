"""Bank of England statistical database (IADB CSV, no key). Issue #7.

Format (verified 18 Nov 2026):
    DATE,IUDBEDR,IUDMNZC
    01 Oct 2026,3.75,5.424
"""

import csv
import io
from datetime import date

from app.collectors.base import CollectorError, get, parse_period, to_float
from app.collectors.macro.catalogue import SeriesSpec
from app.collectors.macro.source import FetchContext, MacroSource
from app.collectors.macro.store import Obs

URL = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"


class BoeSource(MacroSource):
    name = "boe"

    def fetch(self, specs: list[SeriesSpec], ctx: FetchContext) -> dict[str, list[Obs] | Exception]:
        try:
            text = get(self.client, URL, {
                "csv.x": "yes",
                "Datefrom": _boe_date(ctx.since),
                "Dateto": "now",
                "SeriesCodes": ",".join(s.source_id for s in specs),
                "CSVF": "TN",
                "UsingCodes": "Y",
                "VPD": "Y",
                "VFD": "N",
            }, ctx.retry_delay).text
            rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
            if rows and "DATE" not in rows[0]:
                raise CollectorError("Unexpected Bank of England response (no DATE column)")
        except Exception as e:
            return {s.key: e for s in specs}
        out: dict[str, list[Obs] | Exception] = {}
        for spec in specs:
            if rows and spec.source_id not in rows[0]:
                out[spec.key] = KeyError(f"Series {spec.source_id} missing from BoE response")
                continue
            out[spec.key] = [(parse_period(r["DATE"]), to_float(r[spec.source_id])) for r in rows]
        return out


def _boe_date(d: date) -> str:
    return d.strftime("%d/%b/%Y")
