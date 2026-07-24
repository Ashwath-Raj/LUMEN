from typing import Protocol, TypeVar

T = TypeVar("T")


class BaseRepository(Protocol[T]):
    def get(self, identifier: str) -> T | None:
        ...

    def list(self) -> list[T]:
        ...
