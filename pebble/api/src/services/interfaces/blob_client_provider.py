from typing import Protocol

from azure.storage.blob import BlobServiceClient


class BlobClientProvider(Protocol):
    """Azure client boundary: Azurite locally, managed identity in Azure."""

    # Public access level for newly created containers (None = private).
    container_public_access: str | None

    def get_client(self) -> BlobServiceClient: ...

    def build_read_url(self, container: str, name: str) -> str: ...
