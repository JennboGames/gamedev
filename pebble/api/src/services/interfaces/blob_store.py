from typing import Protocol


class BlobStore(Protocol):
    """Stores swatch images and the generated color map."""

    def upload(self, container: str, name: str, data: bytes, content_type: str) -> None: ...

    def read_url(self, container: str, name: str) -> str:
        """A URL the browser can use to display the blob."""
        ...

    def health_check(self) -> bool: ...
