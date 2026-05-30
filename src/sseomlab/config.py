"""설정 로딩: .env (비밀키/옵션) + config/*.yaml (지역·공간유형·점수 가중치)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


class Settings(BaseSettings):
    """.env 기반 런타임 설정."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"
    anthropic_screening_model: str = "claude-haiku-4-5-20251001"

    naver_client_id: str = ""
    naver_client_secret: str = ""

    kosis_api_key: str = ""

    google_service_account_json: str = ""
    google_sheet_id: str = ""

    request_delay_seconds: float = 1.0
    max_places_per_query: int = 100


def _load_yaml(name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_regions() -> dict[str, Any]:
    return _load_yaml("regions.yaml")["regions"]


@lru_cache
def get_space_types() -> dict[str, Any]:
    return _load_yaml("space_types.yaml")


@lru_cache
def get_scoring() -> dict[str, Any]:
    return _load_yaml("scoring.yaml")


@lru_cache
def get_demand() -> dict[str, Any]:
    return _load_yaml("demand.yaml")


@lru_cache
def get_concepts() -> dict[str, Any]:
    return _load_yaml("concepts.yaml")


@lru_cache
def get_sales() -> dict[str, Any]:
    return _load_yaml("sales.yaml")
