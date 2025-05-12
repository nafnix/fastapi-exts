import inspect
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from fastapi import APIRouter, params
from fastapi.routing import APIRoute, APIWebSocketRoute

from fastapi_exts._utils import (
    Is,
    add_parameter,
    list_parameters,
    new_function,
    update_signature,
)

from fastapi_exts.responses import Response, build_responses

from ._utils import iter_class_dependency


T = TypeVar("T")


Fn = TypeVar("Fn", bound=Callable)


class CBV:
    def __init__(
        self,
        router: APIRouter,
    ) -> None:
        self.router = router

    @property
    def get(self):
        return self.router.get

    @property
    def put(self):
        return self.router.put

    @property
    def post(self):
        return self.router.post

    @property
    def delete(self):
        return self.router.delete

    @property
    def patch(self):
        return self.router.patch

    @property
    def trace(self):
        return self.router.trace

    @property
    def websocket(self):
        return self.router.websocket

    @property
    def ws(self):
        return self.router.websocket

    def route_handle(
        self,
        endpoint: Callable,
        handle: Callable[[APIRoute], None | APIRoute],
    ):
        for route in self.router.routes:
            if isinstance(route, APIRoute) and route.endpoint == endpoint:
                handle(route)

    def responses(self, *responses: Response) -> Callable[[Fn], Fn]:
        def decorator(fn: Fn) -> Fn:
            self.route_handle(
                fn,
                lambda route: route.responses.update(
                    build_responses(*responses)
                ),
            )

            return fn

        return decorator

    def _create_class_dependencies(self, cls: type):
        def collect_class_dependencies(**kwds):
            return kwds

        parameters = [
            inspect.Parameter(
                name=name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=dep,
                annotation=typ,
            )
            for name, dep, typ in iter_class_dependency(cls)
        ]

        update_signature(collect_class_dependencies, parameters=parameters)
        return collect_class_dependencies

    @staticmethod
    def _create_class_instance(*, cls: type, name: str, kwds: dict):
        instance = cls()
        class_dependencies_: dict = kwds.pop(name)
        for k, v in class_dependencies_.items():
            setattr(instance, k, v)
        return instance

    def _create_instance_function(self, fn: Callable, cls: type):
        class_dependencies = self._create_class_dependencies(cls)
        name = class_dependencies.__name__

        parameters = add_parameter(
            list_parameters(fn)[1:],
            name=name,
            default=params.Depends(class_dependencies),
        )
        fn = new_function(fn, parameters=parameters)
        if Is.coroutine_function(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwds):
                instance = self._create_class_instance(
                    cls=cls, name=name, kwds=kwds
                )
                return await fn(instance, *args, **kwds)

            return async_wrapper

        @wraps(fn)
        def wrapper(*args, **kwds):
            instance = self._create_class_instance(
                cls=cls, name=name, kwds=kwds
            )
            return fn(instance, *args, **kwds)

        return wrapper

    def __call__(self, cls: type[T], /) -> type[T]:
        api_routes = [
            i
            for i in self.router.routes
            if isinstance(i, APIRoute | APIWebSocketRoute)
        ]
        new_router = APIRouter()
        for route in api_routes:
            fn = route.endpoint

            if hasattr(cls, fn.__name__):
                self.router.routes.remove(route)

                if not isinstance(fn, staticmethod):
                    new_fn = self._create_instance_function(fn, cls)
                    setattr(route, "endpoint", new_fn)

                new_router.routes.append(route)

        self.router.include_router(new_router)

        return cls
