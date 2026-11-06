"""Central configuration. Secrets come from environment variables only (see .env.example)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

VALID_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "1d"}
VALID_TZ = {"America/New_York", "UTC", "Asia/Kolkata"}


class HistoryConfig(BaseModel):
    source: str = "stock_tweets_csv"
    start: str
    end: str
    ticker_in_dataset: str


class AssetConfig(BaseModel):
    symbol: str
    company_name: str
    exchange_timezone: str = "America/New_York"
    bar_interval: str = "1d"
    horizons: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    search_queries: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    lookback_days: int = 180
    history: Optional[HistoryConfig] = None

    @field_validator("bar_interval")
    @classmethod
    def _interval(cls, v: str) -> str:
        if v not in VALID_INTERVALS:
            raise ValueError(f"bar_interval must be one of {sorted(VALID_INTERVALS)}")
        return v

    @field_validator("exchange_timezone")
    @classmethod
    def _tz(cls, v: str) -> str:
        if v not in VALID_TZ:
            raise ValueError(f"exchange_timezone must be one of {sorted(VALID_TZ)}")
        return v

    @field_validator("horizons")
    @classmethod
    def _horizons(cls, v: list[int]) -> list[int]:
        if not v or any(h < 1 for h in v):
            raise ValueError("horizons must be positive integers")
        return sorted(set(v))


class Settings(BaseModel):
    apify_api_token: str = ""
    apify_actor_id: str = ""
    tavily_api_key: str = ""
    database_url: str = f"sqlite:///{(ROOT / 'artifacts' / 'xanalysis.db').as_posix()}"
    log_level: str = "INFO"
    http_timeout_s: float = 60.0
    data_dir: Path = ROOT / "data"
    asset: AssetConfig


def load_asset_config(path: str | Path | None = None) -> AssetConfig:
    p = Path(path or os.getenv("ASSET_CONFIG", ROOT / "config" / "asset_config.yaml"))
    if not p.is_absolute():
        p = ROOT / p
    return AssetConfig(**yaml.safe_load(p.read_text(encoding="utf-8")))


def load_settings(asset_path: str | Path | None = None) -> Settings:
    return Settings(
        apify_api_token=os.getenv("APIFY_API_TOKEN", ""),
        apify_actor_id=os.getenv("APIFY_ACTOR_ID", ""),
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        database_url=os.getenv("DATABASE_URL", Settings.model_fields["database_url"].default),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        asset=load_asset_config(asset_path),
    )
