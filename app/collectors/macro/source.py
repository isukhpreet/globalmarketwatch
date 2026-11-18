"""Base class every macro data source implements (issue #2)."""

from dataclasses import dataclass
from datetime import date

import httpx

from app.collectors.macro.catalogue import SeriesSpec
from app.collectors.macro.store import Obs


@dataclass
class FetchContext:
    since: date            # earliest date worth requesting
    incremental: bool      # True when every series of this source already has data
    api_key: str = ""
    retry_delay: float = 2.0


class MacroSource:
    """Subclasses implement `fetch_one` (one request per series) or override `fetch`
    (one request returning many series, e.g. a whole yield curve)."""

    name: str = ""

    def __init__(self, client: httpx.Client):
        self.client = client

    def fetch(self, specs: list[SeriesSpec], ctx: FetchContext) -> dict[str, list[Obs] | Exception]:
        out: dict[str, list[Obs] | Exception] = {}
        for spec in specs:
            try:
                out[spec.key] = self.fetch_one(spec, ctx)
            except Exception as e:  # one bad series must not stop the others
                out[spec.key] = e
        return out

    def fetch_one(self, spec: SeriesSpec, ctx: FetchContext) -> list[Obs]:
        raise NotImplementedError
