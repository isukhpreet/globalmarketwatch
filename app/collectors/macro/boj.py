"""Bank of Japan Time-Series Data Search API (JSON, no key; launched Feb 2026). Issue #8.

Request: getDataCode?format=json&lang=en&db=<DB>&code=<SERIES>&startDate=<YYYYMM>
Response shape per the BoJ API manual:
    {"STATUS": 200, "MESSAGE": "...", "RESULTSET": [
        {"SERIES_CODE": "...", "VALUES": {"SURVEY_DATES": [20261104, ...], "VALUES": [0.727, ...]}}
    ]}
Not yet verified against live data (marked verified: false in config/series.yaml).
Data credit: Source: Bank of Japan, Time-Series Data Search.
"""

from app.collectors.base import CollectorError, get, parse_period, to_float
from app.collectors.macro.catalogue import SeriesSpec
from app.collectors.macro.source import FetchContext, MacroSource
from app.collectors.macro.store import Obs

URL = "https://www.stat-search.boj.or.jp/api/v1/getDataCode"


class BojSource(MacroSource):
    name = "boj"

    def fetch_one(self, spec: SeriesSpec, ctx: FetchContext) -> list[Obs]:
        data = get(self.client, URL, {
            "format": "json",
            "lang": "en",
            "db": spec.params.get("db", ""),
            "code": spec.source_id,
            "startDate": ctx.since.strftime("%Y%m"),
        }, ctx.retry_delay).json()
        status = data.get("STATUS")
        if status not in (200, "200"):
            raise CollectorError(f"BoJ API status {status}: {data.get('MESSAGE', '')}")
        resultset = data.get("RESULTSET") or []
        if not resultset:
            return []
        vals = resultset[0].get("VALUES") or {}
        dates, values = vals.get("SURVEY_DATES") or [], vals.get("VALUES") or []
        return [(parse_period(d), to_float(v)) for d, v in zip(dates, values, strict=False)]
