"""Office for National Statistics time series (JSON, no key). Issue #7.

params.path is the series page path, e.g. /economy/inflationandpriceindices/timeseries/d7g7/mm23
The JSON has 'months' / 'quarters' / 'years' arrays of {"date": "2026 JAN", "value": "3.0", ...}
(verified 18 Nov 2026).
"""

from app.collectors.base import CollectorError, get, parse_period, to_float
from app.collectors.macro.catalogue import SeriesSpec
from app.collectors.macro.source import FetchContext, MacroSource
from app.collectors.macro.store import Obs

BASE = "https://www.ons.gov.uk"
_ARRAY = {"m": "months", "q": "quarters", "a": "years"}


class OnsSource(MacroSource):
    name = "ons"

    def fetch_one(self, spec: SeriesSpec, ctx: FetchContext) -> list[Obs]:
        path = spec.params.get("path")
        if not path:
            raise CollectorError(f"{spec.key}: ONS series needs params.path")
        data = get(self.client, f"{BASE}{path}/data", None, ctx.retry_delay).json()
        arr = data.get(_ARRAY.get(spec.frequency, "months"))
        if arr is None:
            raise CollectorError(f"No '{_ARRAY.get(spec.frequency)}' array in ONS response")
        since = ctx.since.isoformat()
        obs = [(parse_period(p["date"]), to_float(p.get("value"))) for p in arr]
        return [o for o in obs if o[0] >= since]
