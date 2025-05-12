from typing import Annotated, Protocol, TypeVar

from fastapi import Depends

from fastapi_exts.exceptions import NamedHTTPError


T = TypeVar("T")
E = TypeVar("E", bound=NamedHTTPError)


class Dependency(Protocol[T, E]):
    exceptions: tuple[type[E], ...]
    Type: type[T]


class SyncDependency(Dependency[T, E]):
    def handler(self, *args, **kwargs) -> T: ...


class AsyncDependency(Dependency[T, E]):
    async def handler(self, *args, **kwargs) -> T: ...


DependencyT = TypeVar("DependencyT", bound=SyncDependency | AsyncDependency)


def dependency(
    dependency: type[DependencyT],
) -> type[DependencyT]:
    setattr(
        dependency,
        "Type",
        Annotated[
            dependency.Type,  # type: ignore
            Depends(dependency.handler),
        ],
    )

    return dependency
