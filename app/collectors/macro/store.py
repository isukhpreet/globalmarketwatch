"""Storing observations: transforms and revision detection (issue #10)."""

import sqlite3
from dataclasses import dataclass

Obs = tuple[str, float | None]   # (ISO date, value)


@dataclass
class UpsertResult:
    new: int = 0
    revised: int = 0
    unchanged: int = 0


def apply_transform(obs: list[Obs], transform: str) -> list[Obs]:
    """`yoy`: % change vs the same date one year earlier. Points without a base are dropped."""
    if transform == "none":
        return obs
    if transform == "yoy":
        by_date = {d: v for d, v in obs}
        out: list[Obs] = []
        for d, v in sorted(obs):
            base = by_date.get(f"{int(d[:4]) - 1}{d[4:]}")
            if v is None or not base:
                continue
            out.append((d, round((v / base - 1) * 100, 2)))
        return out
    raise ValueError(f"Unknown transform {transform!r}")


def upsert_observations(
    conn: sqlite3.Connection, series_key: str, obs: list[Obs], now: str
) -> UpsertResult:
    """Insert new points; update changed ones and flag them as revised.

    `released_at` records when we first saw a value (≈ publication time, since collectors run
    just after scheduled releases). Missing values (None) are ignored.
    """
    res = UpsertResult()
    existing = {
        r["obs_date"]: r["value"]
        for r in conn.execute(
            "SELECT obs_date, value FROM macro_obs WHERE series_key = ?", (series_key,)
        )
    }
    deduped = {d: v for d, v in obs}  # a source may repeat a date; the last value wins
    for d, v in sorted(deduped.items()):
        if v is None:
            continue
        if d not in existing:
            conn.execute(
                """INSERT INTO macro_obs(series_key, obs_date, value, released_at, revised,
                                         fetched_at) VALUES (?, ?, ?, ?, 0, ?)""",
                (series_key, d, v, now, now),
            )
            existing[d] = v
            res.new += 1
        elif existing[d] is None or abs(existing[d] - v) > 1e-9:
            conn.execute(
                """UPDATE macro_obs SET value = ?, revised = 1, fetched_at = ?
                   WHERE series_key = ? AND obs_date = ?""",
                (v, now, series_key, d),
            )
            res.revised += 1
        else:
            res.unchanged += 1
    return res
