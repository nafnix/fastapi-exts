from collections.abc import Awaitable, Callable, Coroutine, Sequence
from copy import copy
from typing import Any, Generic, TypeVar, overload

from fastapi import params
from fastapi.dependencies.utils import get_typed_signature

from fastapi_exts._utils import _undefined
from fastapi_exts.interfaces import HTTPErrorInterface
from fastapi_exts.utils import list_parameters, update_signature


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
    @transform_providers
    def a(number=Provider(lambda: 1)):
        return number.value  # -> 1
    ```

    等价实现:

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

    value: T = _undefined

    @overload
    def __init__(
        self,
        dependency: type[T],
        *,
        use_cache: bool = True,
        exceptions: list[type[HTTPErrorInterface]] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        dependency: Callable[..., Coroutine[Any, Any, T]],
        *,
        use_cache: bool = True,
        exceptions: list[type[HTTPErrorInterface]] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        dependency: Callable[..., Awaitable[T]],
        *,
        use_cache: bool = True,
        exceptions: list[type[HTTPErrorInterface]] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        dependency: Callable[..., T],
        *,
        use_cache: bool = True,
        exceptions: list[type[HTTPErrorInterface]] | None = None,
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
        exceptions: list[type[HTTPErrorInterface]] | None = None,
    ) -> None:
        self.dependency = dependency

        if scopes is not None:
            self.depends = params.Security(
                dependency, use_cache=use_cache, scopes=scopes
            )
        else:
            self.depends = params.Depends(dependency, use_cache=use_cache)

        self.exceptions: list[type[HTTPErrorInterface]] = exceptions or []


def create_provider_dependency(provider: Provider):
    def dependency(value=None):
        provider.value = value
        return provider

    parameters = list_parameters(dependency)

    parameters[0] = parameters[0].replace(default=provider.depends)

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
            dependency = create_provider_dependency(provider)
            signature_params[name] = signature_params[name].replace(
                default=params.Depends(
                    dependency,
                    use_cache=provider.depends.use_cache,
                )
            )

            # 递归更新
            transform_providers(provider.dependency)
            continue

    update_signature(fn, parameters=signature_params.values())
    return fn
