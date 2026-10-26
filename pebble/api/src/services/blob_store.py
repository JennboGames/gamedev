from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import ContentSettings

from src.services.interfaces.blob_client_provider import BlobClientProvider


class AzureBlobStore:
    def __init__(self, provider: BlobClientProvider) -> None:
        self._provider = provider
        self._ready_containers: set[str] = set()

    def _ensure_container(self, container: str) -> None:
        if container in self._ready_containers:
            return
        try:
            self._provider.get_client().create_container(
                container, public_access=self._provider.container_public_access
            )
        except ResourceExistsError:
            pass
        self._ready_containers.add(container)

    def upload(self, container: str, name: str, data: bytes, content_type: str) -> None:
        self._ensure_container(container)
        blob = self._provider.get_client().get_blob_client(container, name)
        blob.upload_blob(
            data, overwrite=True, content_settings=ContentSettings(content_type=content_type)
        )

    def read_url(self, container: str, name: str) -> str:
        return self._provider.build_read_url(container, name)

    def health_check(self) -> bool:
        try:
            self._provider.get_client().get_service_properties()
            return True
        except Exception:  # noqa: BLE001
            return False
