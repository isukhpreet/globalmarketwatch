"""Application settings.

Values come from environment variables or a local `.env` file (never committed).
Every setting has a safe default so the app starts with no configuration at all.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_prefix="GMW_",
        extra="ignore",
    )

    # General
    env: str = "dev"  # dev | prod
    log_level: str = "INFO"
    base_currency: str = "GBP"
    timezone: str = "Europe/London"

    # Paths
    db_path: Path = PROJECT_ROOT / "data" / "gmw.sqlite"
    config_dir: Path = PROJECT_ROOT / "config"
    web_dir: Path = PROJECT_ROOT / "web"

    # Scheduler
    heartbeat_seconds: int = 60

    # API keys (filled in later phases; empty = feature disabled)
    fred_api_key: str = ""
    bok_ecos_api_key: str = ""
    finnhub_api_key: str = ""
    alpaca_key_id: str = ""
    alpaca_secret: str = ""
    ig_api_key: str = ""
    ig_username: str = ""
    ig_password: str = ""
    t212_api_key: str = ""
    t212_api_secret: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    github_bridge_token: str = ""

    def enabled_integrations(self) -> dict[str, bool]:
        """Which integrations have credentials configured (values never exposed)."""
        return {
            "fred": bool(self.fred_api_key),
            "bok_ecos": bool(self.bok_ecos_api_key),
            "finnhub": bool(self.finnhub_api_key),
            "alpaca": bool(self.alpaca_key_id and self.alpaca_secret),
            "ig": bool(self.ig_api_key and self.ig_username and self.ig_password),
            "trading212": bool(self.t212_api_key and self.t212_api_secret),
            "telegram": bool(self.telegram_bot_token and self.telegram_chat_id),
            "claude_bridge": bool(self.github_bridge_token),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
