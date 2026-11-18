"""FRED (St. Louis Fed) — US macro series. Needs GMW_FRED_API_KEY. Issue #4."""

from app.collectors.base import CollectorError, get, to_float
from app.collectors.macro.catalogue import SeriesSpec
from app.collectors.macro.source import FetchContext, MacroSource
from app.collectors.macro.store import Obs

URL = "https://api.stlouisfed.org/fred/series/observations"


class FredSource(MacroSource):
    name = "fred"

    def fetch_one(self, spec: SeriesSpec, ctx: FetchContext) -> list[Obs]:
        params = {
            "series_id": spec.source_id,
            "api_key": ctx.api_key,
            "file_type": "json",
            "observation_start": ctx.since.isoformat(),
            **{k: str(v) for k, v in spec.params.items()},
        }
        data = get(self.client, URL, params, ctx.retry_delay).json()
        if "observations" not in data:
            raise CollectorError(data.get("error_message", "No observations in FRED response"))
        return [(o["date"], to_float(o["value"])) for o in data["observations"]]
