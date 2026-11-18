"""Macro series catalogue: loads and validates config/series.yaml (issue #3)."""

import sqlite3
from pathlib import Path
from typing import Literal

import yaml
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field, field_validator, model_validator


class SourceSpec(BaseModel):
    name: str
    key: str | None = None            # settings attribute holding the API key
    schedule: list[str] = Field(default_factory=list)

    @field_validator("schedule")
    @classmethod
    def _valid_cron(cls, v: list[str]) -> list[str]:
        for expr in v:
            CronTrigger.from_crontab(expr)  # raises ValueError if invalid
        return v


class SeriesSpec(BaseModel):
    key: str
    name: str
    region: Literal["US", "EU", "UK", "JP", "KR", "GLOBAL"]
    unit: str | None = None
    frequency: Literal["d", "w", "m", "q", "a"]
    source: str
    source_id: str
    params: dict = Field(default_factory=dict)
    transform: Literal["none", "yoy"] = "none"
    verified: bool = True


class Catalogue(BaseModel):
    sources: dict[str, SourceSpec]
    series: list[SeriesSpec]

    @model_validator(mode="before")
    @classmethod
    def _name_sources(cls, data: dict) -> dict:
        for name, spec in (data.get("sources") or {}).items():
            spec.setdefault("name", name)
        return data

    @model_validator(mode="after")
    def _check(self) -> "Catalogue":
        keys = [s.key for s in self.series]
        dupes = {k for k in keys if keys.count(k) > 1}
        if dupes:
            raise ValueError(f"Duplicate series keys: {sorted(dupes)}")
        unknown = {s.source for s in self.series} - set(self.sources)
        if unknown:
            raise ValueError(f"Series reference unknown sources: {sorted(unknown)}")
        return self

    def for_source(self, source: str) -> list[SeriesSpec]:
        return [s for s in self.series if s.source == source]


def load_catalogue(path: Path) -> Catalogue:
    return Catalogue.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def seed_series(conn: sqlite3.Connection, cat: Catalogue) -> int:
    for s in cat.series:
        conn.execute(
            """INSERT INTO macro_series(series_key, name, region, unit, frequency, source,
                                         source_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(series_key) DO UPDATE SET name=excluded.name, region=excluded.region,
                 unit=excluded.unit, frequency=excluded.frequency, source=excluded.source,
                 source_id=excluded.source_id""",
            (s.key, s.name, s.region, s.unit, s.frequency, s.source, s.source_id),
        )
    return len(cat.series)
