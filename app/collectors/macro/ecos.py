"""Bank of Korea ECOS Open API (JSON). Needs GMW_BOK_ECOS_API_KEY. Issue #9.

URL: /api/StatisticSearch/{key}/json/en/{from}/{to}/{stat}/{cycle}/{start}/{end}/{item}
Response (verified 18 Nov 2026 with stat codes 722Y001, 901Y009, 817Y002):
    {"StatisticSearch": {"list_total_count": N,
                         "row": [{"TIME": "202601", "DATA_VALUE": "2.5", ...}]}}
No data:  {"RESULT": {"CODE": "INFO-200", "MESSAGE": "..."}}
"""

from datetime import date

from app.collectors.base import CollectorError, get, parse_period, to_float
from app.collectors.macro.catalogue import SeriesSpec
from app.collectors.macro.source import FetchContext, MacroSource
from app.collectors.macro.store import Obs

URL = "https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/en/1/100000/{stat}/{cycle}/{start}/{end}/{item}"


def ecos_period(d: date, cycle: str) -> str:
    return {
        "D": d.strftime("%Y%m%d"),
        "M": d.strftime("%Y%m"),
        "Q": f"{d.year}Q{(d.month - 1) // 3 + 1}",
        "A": str(d.year),
    }[cycle]


class EcosSource(MacroSource):
    name = "ecos"

    def fetch_one(self, spec: SeriesSpec, ctx: FetchContext) -> list[Obs]:
        cycle = spec.params.get("cycle", "M")
        url = URL.format(
            key=ctx.api_key, stat=spec.source_id, cycle=cycle,
            start=ecos_period(ctx.since, cycle), end=ecos_period(date.today(), cycle),
            item=spec.params.get("item", ""),
        )
        data = get(self.client, url, None, ctx.retry_delay).json()
        if "RESULT" in data:
            code = data["RESULT"].get("CODE", "")
            if code == "INFO-200":  # no data for the period
                return []
            raise CollectorError(f"ECOS {code}: {data['RESULT'].get('MESSAGE', '')}")
        rows = (data.get("StatisticSearch") or {}).get("row") or []
        return [(parse_period(r["TIME"]), to_float(r.get("DATA_VALUE"))) for r in rows]
