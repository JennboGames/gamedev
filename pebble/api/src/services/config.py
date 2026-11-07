"""Flat app configuration. Environment is read once in the composition root (registry)."""

import os
from dataclasses import dataclass
from pathlib import Path

from src.errors.error_types import ConfigurationError

DEVELOPMENT = "Development"
DEFAULT_CATALOG_PATH = Path(__file__).resolve().parents[3] / "catalog" / "products.json"


def require_setting(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class AppConfig:
    environment: str
    # Local (Development only)
    storage_connection_string: str | None
    database_url: str | None
    # Production (managed identity)
    azure_storage_account: str | None
    azure_postgres_host: str | None
    azure_postgres_database: str | None
    azure_postgres_user: str | None
    # Tuning
    max_shades_per_product: int
    extraction_workers: int
    catalog_path: Path = DEFAULT_CATALOG_PATH

    @property
    def is_development(self) -> bool:
        return self.environment == DEVELOPMENT


def _optional(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if value < 1:
        raise ConfigurationError(f"{name} must be at least 1")
    return value


def load_config() -> AppConfig:
    # Missing or unknown environment means production, never Development.
    return AppConfig(
        environment=os.environ.get("AZURE_FUNCTIONS_ENVIRONMENT", "Production"),
        storage_connection_string=_optional("STORAGE_CONNECTION_STRING"),
        database_url=_optional("DATABASE_URL"),
        azure_storage_account=_optional("AZURE_STORAGE_ACCOUNT"),
        azure_postgres_host=_optional("AZURE_POSTGRES_HOST"),
        azure_postgres_database=_optional("AZURE_POSTGRES_DATABASE"),
        azure_postgres_user=_optional("AZURE_POSTGRES_USER"),
        max_shades_per_product=_positive_int("MAX_SHADES_PER_PRODUCT", 60),
        extraction_workers=_positive_int("EXTRACTION_WORKERS", 8),
        catalog_path=Path(os.environ.get("CATALOG_PATH") or DEFAULT_CATALOG_PATH),
    )
