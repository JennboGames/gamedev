"""Flat app configuration. Environment is read once in the composition root (registry)."""

import os
from dataclasses import dataclass

from src.errors.error_types import ConfigurationError

DEVELOPMENT = "Development"
# Estée Lauder Double Wear, Armani Luminous Silk, Westmore Beauty, L'Oréal True Match,
# tarte BB blur (fair), Lancôme Teint Idole, NARS Natural Radiant Longwear
DEFAULT_PINNED_ASINS = (
    "B0GQVP8RLD,B0028P5TOW,B0HC436QM3,B0BFRV3GCS,B00AVUDDC6,B0BNWBT2G2,B078QZDJFB"
)


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
    # Amazon PA-API (Essential, external; validated when used)
    amazon_access_key: str | None
    amazon_secret_key: str | None
    amazon_partner_tag: str | None
    amazon_host: str
    amazon_region: str
    amazon_marketplace: str
    # Tuning
    max_shades_per_product: int
    extraction_workers: int
    # ASINs always included in a search, ahead of the keyword results
    pinned_asins: tuple[str, ...] = ()

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


def _asin_list(name: str, default: str) -> tuple[str, ...]:
    raw = os.environ.get(name)
    raw = default if raw is None else raw
    return tuple(dict.fromkeys(a.strip().upper() for a in raw.split(",") if a.strip()))


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
        amazon_access_key=_optional("AMAZON_PAAPI_ACCESS_KEY"),
        amazon_secret_key=_optional("AMAZON_PAAPI_SECRET_KEY"),
        amazon_partner_tag=_optional("AMAZON_PARTNER_TAG"),
        amazon_host=os.environ.get("AMAZON_PAAPI_HOST", "webservices.amazon.com"),
        amazon_region=os.environ.get("AMAZON_PAAPI_REGION", "us-east-1"),
        amazon_marketplace=os.environ.get("AMAZON_PAAPI_MARKETPLACE", "www.amazon.com"),
        max_shades_per_product=_positive_int("MAX_SHADES_PER_PRODUCT", 60),
        extraction_workers=_positive_int("EXTRACTION_WORKERS", 8),
        pinned_asins=_asin_list("PINNED_ASINS", DEFAULT_PINNED_ASINS),
    )
