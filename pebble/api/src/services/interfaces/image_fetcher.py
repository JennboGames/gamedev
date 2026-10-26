from typing import Protocol

from src.models.domain import FetchedImage


class ImageFetcher(Protocol):
    def fetch(self, url: str) -> FetchedImage: ...
