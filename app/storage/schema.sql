-- GlobalMarketWatch schema, version 1.
-- Every table from architecture §8 is created up front so later phases add data, not migrations.
-- Timestamps are ISO-8601 UTC strings.

CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
);

-- Instruments: one row per tradable thing, with symbol mappings per data source.
CREATE TABLE IF NOT EXISTS instruments (
    id              INTEGER PRIMARY KEY,
    key             TEXT NOT NULL UNIQUE,         -- our own stable id, e.g. 'IDX.SPX'
    name            TEXT NOT NULL,
    asset_class     TEXT NOT NULL,                -- equity | etf | index | fx | bond_future | commodity | crypto | volatility
    region          TEXT,                         -- US | EU | UK | JP | KR | GLOBAL
    currency        TEXT,
    exchange        TEXT,
    sector          TEXT,
    t212_ticker     TEXT,
    finnhub_symbol  TEXT,
    ig_epic         TEXT,
    yf_symbol       TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

-- Dynamic watchlist (M10).
CREATE TABLE IF NOT EXISTS watchlist (
    id              INTEGER PRIMARY KEY,
    instrument_key  TEXT NOT NULL REFERENCES instruments(key),
    entry_type      TEXT NOT NULL,                -- core | holding | pinned | auto | claude
    reason          TEXT,
    status          TEXT NOT NULL DEFAULT 'active', -- active | suggested | dismissed
    added_at        TEXT NOT NULL,
    expires_at      TEXT,
    UNIQUE (instrument_key, entry_type)
);

CREATE TABLE IF NOT EXISTS watch_tiers (
    instrument_key  TEXT PRIMARY KEY REFERENCES instruments(key),
    tier            TEXT NOT NULL,                -- live | fast | slow
    source          TEXT,
    priority        REAL,
    changed_at      TEXT NOT NULL
);

-- Prices (M2).
CREATE TABLE IF NOT EXISTS prices_tick (
    instrument_key  TEXT NOT NULL,
    ts              TEXT NOT NULL,
    price           REAL NOT NULL,
    bid             REAL,
    ask             REAL,
    volume          REAL,
    source          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tick_key_ts ON prices_tick(instrument_key, ts);

CREATE TABLE IF NOT EXISTS prices_bar (
    instrument_key  TEXT NOT NULL,
    interval        TEXT NOT NULL,                -- 1m | 1d
    ts              TEXT NOT NULL,
    open REAL, high REAL, low REAL, close REAL, volume REAL,
    source          TEXT NOT NULL,
    PRIMARY KEY (instrument_key, interval, ts)
);

-- Macro (M3).
CREATE TABLE IF NOT EXISTS macro_series (
    series_key      TEXT PRIMARY KEY,             -- e.g. 'US.CPI.YOY'
    name            TEXT NOT NULL,
    region          TEXT NOT NULL,
    unit            TEXT,
    frequency       TEXT,                         -- d | w | m | q
    source          TEXT NOT NULL,
    source_id       TEXT NOT NULL                 -- id at the source, e.g. FRED 'CPIAUCSL'
);

CREATE TABLE IF NOT EXISTS macro_obs (
    series_key      TEXT NOT NULL REFERENCES macro_series(series_key),
    obs_date        TEXT NOT NULL,
    value           REAL,
    released_at     TEXT,
    revised         INTEGER NOT NULL DEFAULT 0,
    fetched_at      TEXT NOT NULL,
    PRIMARY KEY (series_key, obs_date)
);

-- News and events (M4).
CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY,
    event_type      TEXT NOT NULL,                -- release | central_bank | earnings | political | other
    region          TEXT,
    title           TEXT NOT NULL,
    scheduled_at    TEXT NOT NULL,
    importance      INTEGER,                      -- 1 low .. 3 high
    consensus       TEXT,
    actual          TEXT,
    linked_instruments TEXT,                      -- JSON list of instrument keys
    source          TEXT,
    UNIQUE (title, scheduled_at)
);

CREATE TABLE IF NOT EXISTS news (
    id              INTEGER PRIMARY KEY,
    published_at    TEXT NOT NULL,
    source          TEXT NOT NULL,
    headline        TEXT NOT NULL,
    url             TEXT,
    tags            TEXT,                         -- JSON: tickers, regions, topics
    cluster_id      TEXT,                         -- groups duplicates of one story
    impact_score    REAL,
    severity        TEXT,                         -- critical | high | watch
    fetched_at      TEXT NOT NULL,
    UNIQUE (source, url)
);

-- Portfolio (M7).
CREATE TABLE IF NOT EXISTS accounts (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    kind            TEXT NOT NULL,                -- t212_invest | t212_isa | manual
    currency        TEXT NOT NULL DEFAULT 'GBP'
);

CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY,
    account_id      INTEGER NOT NULL REFERENCES accounts(id),
    instrument_key  TEXT,
    tx_type         TEXT NOT NULL,                -- buy | sell | dividend | deposit | withdrawal | fee | interest
    ts              TEXT NOT NULL,
    quantity        REAL,
    price           REAL,
    amount          REAL,
    currency        TEXT,
    source          TEXT NOT NULL,                -- api | csv | manual
    source_id       TEXT,                         -- Trading 212 order/transaction id
    UNIQUE (account_id, source_id)
);

CREATE TABLE IF NOT EXISTS positions (
    account_id      INTEGER NOT NULL REFERENCES accounts(id),
    instrument_key  TEXT NOT NULL,
    quantity        REAL NOT NULL,
    avg_price       REAL,
    currency        TEXT,
    manual_value    REAL,                         -- for assets without a price feed
    source          TEXT NOT NULL,
    last_synced     TEXT NOT NULL,
    PRIMARY KEY (account_id, instrument_key)
);

-- Alerts (M6).
CREATE TABLE IF NOT EXISTS alerts_rules (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    rule_type       TEXT NOT NULL,
    params          TEXT NOT NULL,                -- JSON
    enabled         INTEGER NOT NULL DEFAULT 1,
    cooldown_min    INTEGER NOT NULL DEFAULT 60
);

CREATE TABLE IF NOT EXISTS alerts_log (
    id              INTEGER PRIMARY KEY,
    rule_id         INTEGER REFERENCES alerts_rules(id),
    fired_at        TEXT NOT NULL,
    severity        TEXT NOT NULL,
    message         TEXT NOT NULL,
    delivered       INTEGER NOT NULL DEFAULT 0
);

-- AI analyst (M8).
CREATE TABLE IF NOT EXISTS briefings (
    id              INTEGER PRIMARY KEY,
    kind            TEXT NOT NULL,                -- morning | weekly | event
    engine          TEXT NOT NULL,                -- claude | template
    created_at      TEXT NOT NULL,
    pack_ts         TEXT,
    body_md         TEXT NOT NULL
);

-- Health of every collector, stream and bridge.
CREATE TABLE IF NOT EXISTS collector_status (
    name            TEXT PRIMARY KEY,
    last_success    TEXT,
    last_error      TEXT,
    last_error_msg  TEXT,
    detail          TEXT
);
