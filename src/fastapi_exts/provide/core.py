from collections.abc import Awaitable, Callable, Coroutine, Sequence
from typing import Any, Generic, TypeVar, cast, overload

from fastapi import params

from fastapi_exts.utils.responses import ResponseProtocol


T = TypeVar("T")


class Provide(Generic[T]):
    @overload
    def __new__(
        cls,
        dependency: type[T],
        *,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T: ...

    @overload
    def __new__(
        cls,
        dependency: Callable[..., Coroutine[Any, Any, T]],
        *,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T: ...

    @overload
    def __new__(
        cls,
        dependency: Callable[..., Awaitable[T]],
        *,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T: ...

    @overload
    def __new__(
        cls,
        dependency: Callable[..., T],
        *,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T: ...

    depends: params.Depends
    responses: list[type[ResponseProtocol]]

    def __new__(
        cls,
        dependency: type[T]
        | Callable[..., T]
        | Callable[..., Awaitable[T]]
        | Callable[..., Coroutine[Any, Any, T]],
        *,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T:
        result = super().__new__(cls)
        result.depends = params.Depends(dependency, use_cache=use_cache)

        result.responses = responses or []
        return result  # type: ignore


class SecurityProvide(Provide[T], Generic[T]):
    depends: params.Security

    @overload
    def __new__(
        cls,
        dependency: type[T],
        *,
        scopes: Sequence[str] | None = None,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T: ...

    @overload
    def __new__(
        cls,
        dependency: Callable[..., Coroutine[Any, Any, T]],
        *,
        scopes: Sequence[str] | None = None,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T: ...

    @overload
    def __new__(
        cls,
        dependency: Callable[..., Awaitable[T]],
        *,
        scopes: Sequence[str] | None = None,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T: ...

    @overload
    def __new__(
        cls,
        dependency: Callable[..., T],
        *,
        scopes: Sequence[str] | None = None,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T: ...

    def __new__(
        cls,
        dependency: type[T]
        | Callable[..., T]
        | Callable[..., Awaitable[T]]
        | Callable[..., Coroutine[Any, Any, T]],
        *,
        scopes: Sequence[str] | None = None,
        use_cache: bool = True,
        responses: list[type[ResponseProtocol]] | None = None,
    ) -> T:
        result = cast(
            Provide[T],
            super().__new__(
                cls,
                dependency,
                use_cache=use_cache,
                responses=responses,
            ),
        )
        result.depends = params.Security(
            dependency,
            scopes=scopes,
            use_cache=use_cache,
        )

        return result  # type: ignore
