"""ECB Data Portal (SDMX REST, CSV, no key). Issue #6.

source_id is '<dataflow>/<series key>', e.g. 'ICP/M.U2.N.000000.4.ANR'.
The CSV has named columns; we read TIME_PERIOD and OBS_VALUE.
"""

import csv
import io

from app.collectors.base import CollectorError, get, parse_period, to_float
from app.collectors.macro.catalogue import SeriesSpec
from app.collectors.macro.source import FetchContext, MacroSource
from app.collectors.macro.store import Obs

URL = "https://data-api.ecb.europa.eu/service/data/{sid}"


class EcbSource(MacroSource):
    name = "ecb"

    def fetch_one(self, spec: SeriesSpec, ctx: FetchContext) -> list[Obs]:
        r = get(self.client, URL.format(sid=spec.source_id), {
            "format": "csvdata",
            "detail": "dataonly",
            "startPeriod": ctx.since.isoformat(),
        }, ctx.retry_delay)
        reader = csv.DictReader(io.StringIO(r.text.lstrip("﻿")))
        if not reader.fieldnames or "OBS_VALUE" not in reader.fieldnames:
            raise CollectorError("Unexpected ECB response (no OBS_VALUE column)")
        return [(parse_period(row["TIME_PERIOD"]), to_float(row["OBS_VALUE"])) for row in reader]
