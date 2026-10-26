"""PostgreSQL connection providers: local URL for explicit Development, Entra token otherwise."""

import psycopg2
from azure.identity import DefaultAzureCredential

from src.errors.error_types import ConfigurationError
from src.services.config import AppConfig
from src.services.interfaces.connection_provider import DatabaseConnectionProvider

_POSTGRES_ENTRA_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"


class LocalPostgresConnectionProvider:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def connect(self):  # noqa: ANN201
        return psycopg2.connect(self._database_url)


class ManagedIdentityPostgresConnectionProvider:
    """Azure Database for PostgreSQL; the access token is the password, so no secret is stored."""

    def __init__(self, host: str, database: str, user: str) -> None:
        self._host = host
        self._database = database
        self._user = user
        self._credential = DefaultAzureCredential()

    def connect(self):  # noqa: ANN201
        token = self._credential.get_token(_POSTGRES_ENTRA_SCOPE).token
        return psycopg2.connect(
            host=self._host,
            dbname=self._database,
            user=self._user,
            password=token,
            sslmode="require",
        )


def create_connection_provider(config: AppConfig) -> DatabaseConnectionProvider:
    if config.is_development:
        if not config.database_url:
            raise ConfigurationError("Missing required environment variable: DATABASE_URL")
        return LocalPostgresConnectionProvider(config.database_url)

    missing = [
        name
        for name, value in (
            ("AZURE_POSTGRES_HOST", config.azure_postgres_host),
            ("AZURE_POSTGRES_DATABASE", config.azure_postgres_database),
            ("AZURE_POSTGRES_USER", config.azure_postgres_user),
        )
        if not value
    ]
    if missing:
        raise ConfigurationError(f"Missing required environment variables: {', '.join(missing)}")
    return ManagedIdentityPostgresConnectionProvider(
        config.azure_postgres_host,  # type: ignore[arg-type]
        config.azure_postgres_database,  # type: ignore[arg-type]
        config.azure_postgres_user,  # type: ignore[arg-type]
    )
