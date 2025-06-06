import inspect
from collections.abc import Awaitable, Callable
from copy import copy
from types import CoroutineType
from typing import Any, Generic, TypeVar, cast, overload

from fastapi import params
from fastapi.dependencies.utils import get_typed_signature

from fastapi_exts.interfaces import BaseHTTPError
from fastapi_exts.utils import update_signature


class _Undefined: ...


T = TypeVar("T")


class Provider(Generic[T]):
    """创建一个依赖

    :param Generic: 依赖值类型

    示例:

    ```python
    from fastapi import FastAPI
    from fastapi_exts.provider import Provider, parse_providers

    app = FastAPI()


    @app.get("/")
    @parse_providers
    def a(number=Provider(lambda: 1)):
        return number.value  # -> 1
    ```

    类似实现:

    ```python
    from fastapi import FastAPI, Depends
    from typing import Generic, TypeVar

    app = FastAPI()

    T = TypeVar("T")


    class ValueDep(Generic[T]):
        def __init__(self, value: T):
            self.value: T = value


    def get_number_dep(value: int = Depends(lambda: 1)):
        return ValueDep(value)


    @app.get("/")
    def a(number: ValueDep[int] = Depends(get_number_dep)):
        return number.value  # -> 1
    ```
    """

    @overload
    def __init__(
        self,
        dependency: Callable[..., CoroutineType[Any, Any, T]],
        *,
        use_cache: bool = True,
        exceptions: list[type[BaseHTTPError]] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        dependency: Callable[..., Awaitable[T]],
        *,
        use_cache: bool = True,
        exceptions: list[type[BaseHTTPError]] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        dependency: Callable[..., T],
        *,
        use_cache: bool = True,
        exceptions: list[type[BaseHTTPError]] | None = None,
    ) -> None: ...

    def __init__(
        self,
        dependency: Callable[..., T]
        | Callable[..., Awaitable[T]]
        | Callable[..., CoroutineType[Any, Any, T]],
        *,
        use_cache: bool = True,
        exceptions: list[type[BaseHTTPError]] | None = None,
    ) -> None:
        self.dependency = dependency
        self.use_cache = use_cache
        self.exceptions: list[type[BaseHTTPError]] = exceptions or []
        self.value: T = cast(T, _Undefined)


def _create_provider_dependency(provider: Provider):
    def dependency(value=None):
        provider.value = value
        return provider

    parameters = list(inspect.signature(dependency).parameters.values())

    parameters[0] = parameters[0].replace(
        default=params.Depends(
            provider.dependency,
            use_cache=provider.use_cache,
        )
    )

    update_signature(dependency, parameters=parameters)
    return dependency


def _analyze_provider(*, value: Any) -> None | Provider:
    provider = None
    if isinstance(value, Provider):
        provider = copy(value)

    return provider


def transform_providers(fn: Callable):
    """分析并更新函数签名"""

    endpoint_signature = get_typed_signature(fn)
    signature_params = dict(endpoint_signature.parameters.copy())

    for name, param in signature_params.items():
        provider = _analyze_provider(value=param.default)
        if provider is not None:
            dependency = _create_provider_dependency(provider)
            signature_params[name] = signature_params[name].replace(
                default=params.Depends(
                    dependency,
                    use_cache=provider.use_cache,
                )
            )

            # 递归更新
            transform_providers(provider.dependency)
            continue

    update_signature(fn, parameters=signature_params.values())
    return fn
