"""Azure Blob client providers: Azurite for explicit Development, managed identity otherwise."""

from datetime import datetime, timedelta, timezone

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas

from src.errors.error_types import ConfigurationError
from src.services.config import AppConfig
from src.services.interfaces.blob_client_provider import BlobClientProvider

_SAS_LIFETIME = timedelta(hours=1)


class AzuriteBlobClientProvider:
    """Local emulator; containers are public-read so the browser can show the map image."""

    container_public_access: str | None = "blob"

    def __init__(self, connection_string: str) -> None:
        self._client = BlobServiceClient.from_connection_string(connection_string)

    def get_client(self) -> BlobServiceClient:
        return self._client

    def build_read_url(self, container: str, name: str) -> str:
        return self._client.get_blob_client(container, name).url


class ManagedIdentityBlobClientProvider:
    """Azure Storage via DefaultAzureCredential; read URLs are short-lived user-delegation SAS."""

    container_public_access: str | None = None

    def __init__(self, account_name: str) -> None:
        self._client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=DefaultAzureCredential(),
        )

    def get_client(self) -> BlobServiceClient:
        return self._client

    def build_read_url(self, container: str, name: str) -> str:
        now = datetime.now(timezone.utc)
        expiry = now + _SAS_LIFETIME
        key = self._client.get_user_delegation_key(now - timedelta(minutes=5), expiry)
        sas = generate_blob_sas(
            account_name=self._client.account_name,
            container_name=container,
            blob_name=name,
            user_delegation_key=key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
        )
        return f"{self._client.url.rstrip('/')}/{container}/{name}?{sas}"


def create_blob_client_provider(config: AppConfig) -> BlobClientProvider:
    if config.is_development:
        if not config.storage_connection_string:
            raise ConfigurationError(
                "Missing required environment variable: STORAGE_CONNECTION_STRING"
            )
        return AzuriteBlobClientProvider(config.storage_connection_string)

    if not config.azure_storage_account:
        raise ConfigurationError("Missing required environment variable: AZURE_STORAGE_ACCOUNT")
    return ManagedIdentityBlobClientProvider(config.azure_storage_account)
