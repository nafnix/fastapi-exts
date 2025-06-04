import inspect
from collections.abc import Callable, Sequence
from copy import copy
from typing import Generic, TypeVar, cast

from fastapi import Depends

from fastapi_exts._utils import update_signature
from fastapi_exts.interfaces import HTTPError


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

    def __init__(
        self,
        dependency: Callable[..., T],
        *,
        use_cache: bool = True,
        exceptions: Sequence[type[HTTPError]] | None = None,
    ) -> None:
        self.dependency = dependency
        self.use_cache = use_cache
        self.exceptions: Sequence[type[HTTPError]] = exceptions or []
        self.value: T = cast(T, _Undefined)


def _create_dependency(provider: Provider):
    def dependency(value=None):
        provider.value = value
        return provider

    parameters = list(inspect.signature(dependency).parameters.values())

    parameters[0] = parameters[0].replace(
        default=Depends(
            provider.dependency,
            use_cache=provider.use_cache,
        )
    )

    update_signature(dependency, parameters=parameters)
    return dependency


def parse_providers(fn, handler: Callable[[Provider], None] | None = None):
    parameters = list(inspect.signature(fn).parameters.copy().values())
    for index, p in enumerate(parameters):
        provider = p.default
        if isinstance(provider, Provider):
            new_provider = copy(provider)
            dependency = _create_dependency(new_provider)
            parameters[index] = p.replace(default=Depends(dependency))
            if handler:
                handler(new_provider)

    update_signature(fn, parameters=parameters)
    return fn
