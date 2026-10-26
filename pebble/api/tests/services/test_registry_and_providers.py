import pytest

from src.errors.error_types import ConfigurationError
from src.services.blob_providers import (
    AzuriteBlobClientProvider,
    ManagedIdentityBlobClientProvider,
    create_blob_client_provider,
)
from src.services.image_fetcher import HttpImageFetcher
from src.services.postgres_providers import (
    LocalPostgresConnectionProvider,
    ManagedIdentityPostgresConnectionProvider,
    create_connection_provider,
)
from src.services.registry import ServiceRegistry, clear_services, get_services, register_services
from tests.mocks.config import make_config

AZURITE = "UseDevelopmentStorage=true"
LOCAL_DB = "postgresql://user:pass@localhost:5432/foundationdb"


def test_explicit_development_selects_local_providers():
    config = make_config(
        environment="Development", storage_connection_string=AZURITE, database_url=LOCAL_DB
    )

    assert isinstance(create_blob_client_provider(config), AzuriteBlobClientProvider)
    assert isinstance(create_connection_provider(config), LocalPostgresConnectionProvider)


@pytest.mark.parametrize("environment", ["Production", "Staging", "development", ""])
def test_any_other_environment_selects_managed_identity(environment):
    config = make_config(
        environment=environment,
        storage_connection_string=AZURITE,
        database_url=LOCAL_DB,
        azure_storage_account="pebblestore",
        azure_postgres_host="pebble.postgres.database.azure.com",
        azure_postgres_database="foundationdb",
        azure_postgres_user="pebble-api",
    )

    assert isinstance(create_blob_client_provider(config), ManagedIdentityBlobClientProvider)
    assert isinstance(create_connection_provider(config), ManagedIdentityPostgresConnectionProvider)


def test_production_never_falls_back_to_local_settings():
    config = make_config(
        environment="Production", storage_connection_string=AZURITE, database_url=LOCAL_DB
    )

    with pytest.raises(ConfigurationError):
        create_blob_client_provider(config)
    with pytest.raises(ConfigurationError):
        create_connection_provider(config)


def test_development_requires_local_settings():
    config = make_config(environment="Development")

    with pytest.raises(ConfigurationError):
        create_blob_client_provider(config)
    with pytest.raises(ConfigurationError):
        create_connection_provider(config)


def test_get_services_auto_initializes_without_amazon_credentials(monkeypatch):
    clear_services()
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
    monkeypatch.setenv("STORAGE_CONNECTION_STRING", AZURITE)
    monkeypatch.setenv("DATABASE_URL", LOCAL_DB)
    for name in ("AMAZON_PAAPI_ACCESS_KEY", "AMAZON_PAAPI_SECRET_KEY", "AMAZON_PARTNER_TAG"):
        monkeypatch.delenv(name, raising=False)

    try:
        services = get_services()
        assert services.product_search.health_check() is False
        assert get_services() is services
    finally:
        clear_services()


def test_registered_services_take_priority_over_auto_initialization(services):
    assert get_services() is services
    other = ServiceRegistry(**{**services.__dict__})
    register_services(other)
    assert get_services() is other


@pytest.mark.parametrize(
    "url",
    [
        "http://m.media-amazon.com/images/I/a.jpg",
        "https://evil.example.com/a.jpg",
        "https://media-amazon.com.evil.example.com/a.jpg",
        "file:///etc/passwd",
    ],
)
def test_image_fetcher_rejects_non_amazon_or_non_https_urls(url):
    from src.errors.error_types import UpstreamError

    with pytest.raises(UpstreamError):
        HttpImageFetcher().fetch(url)
