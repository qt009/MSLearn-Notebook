from typing import Protocol, runtime_checkable

from app.core.domain.models import UnitContent


@runtime_checkable
class ContentFetcher(Protocol):
    async def fetch(self, url: str) -> str: ...


@runtime_checkable
class UnitParser(Protocol):
    def parse_unit(self, html: str, url: str) -> UnitContent: ...


class ProgressCallback(Protocol):
    def __call__(self, step: str, progress: float, detail: str = "") -> None: ...
