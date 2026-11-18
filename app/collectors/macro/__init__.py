"""Macro collectors (M3): one module per official data source."""

from app.collectors.macro.boe import BoeSource
from app.collectors.macro.boj import BojSource
from app.collectors.macro.ecb import EcbSource
from app.collectors.macro.ecos import EcosSource
from app.collectors.macro.fred import FredSource
from app.collectors.macro.mof import MofSource
from app.collectors.macro.ons import OnsSource
from app.collectors.macro.source import MacroSource
from app.collectors.macro.treasury import TreasurySource

SOURCES: dict[str, type[MacroSource]] = {
    cls.name: cls
    for cls in (FredSource, TreasurySource, EcbSource, BoeSource, OnsSource,
                MofSource, BojSource, EcosSource)
}
