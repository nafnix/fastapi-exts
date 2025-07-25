from collections.abc import Awaitable, Callable, Coroutine, Sequence
from typing import Any, Generic, TypeVar, overload

from fastapi import params

from fastapi_exts._utils import _undefined

from .responses import ResponseInfoInterface


T = TypeVar("T")


class Provider(Generic[T]):
    value: T = _undefined

    @overload
    def __init__(
        self,
        dependency: type[T],
        *,
        use_cache: bool = True,
        responses: list[type[ResponseInfoInterface]] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        dependency: Callable[..., Coroutine[Any, Any, T]],
        *,
        use_cache: bool = True,
        responses: list[type[ResponseInfoInterface]] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        dependency: Callable[..., Awaitable[T]],
        *,
        use_cache: bool = True,
        responses: list[type[ResponseInfoInterface]] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        dependency: Callable[..., T],
        *,
        use_cache: bool = True,
        responses: list[type[ResponseInfoInterface]] | None = None,
    ) -> None: ...

    def __init__(
        self,
        dependency: type[T]
        | Callable[..., T]
        | Callable[..., Awaitable[T]]
        | Callable[..., Coroutine[Any, Any, T]],
        *,
        use_cache: bool = True,
        scopes: Sequence[str] | None = None,
        responses: list[type[ResponseInfoInterface]] | None = None,
    ) -> None:
        if scopes is not None:
            self.depends = params.Security(
                dependency,
                use_cache=use_cache,
                scopes=scopes,
            )
        else:
            self.depends = params.Depends(
                dependency,
                use_cache=use_cache,
            )

        self.responses = responses or []
