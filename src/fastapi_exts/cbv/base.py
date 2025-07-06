import inspect
from collections.abc import Callable
from functools import wraps
from typing import Annotated, TypeVar

from fastapi import APIRouter, FastAPI, params
from fastapi.routing import APIRoute, APIWebSocketRoute

from fastapi_exts._utils import Is, new_function
from fastapi_exts.cbv._utils import iter_class_dependency
from fastapi_exts.provider import Provider
from fastapi_exts.responses import Response, build_responses
from fastapi_exts.routing import ExtAPIRouter, analyze_and_update
from fastapi_exts.utils import (
    inject_parameter,
    list_parameters,
    update_signature,
)


T = TypeVar("T")


Fn = TypeVar("Fn", bound=Callable)


class CBV:
    def __init__(self, router: APIRouter | FastAPI, /) -> None:
        self.router = router
        self._router = ExtAPIRouter()

    @property
    def get(self):
        return self._router.get

    @property
    def put(self):
        return self._router.put

    @property
    def post(self):
        return self._router.post

    @property
    def delete(self):
        return self._router.delete

    @property
    def patch(self):
        return self._router.patch

    @property
    def trace(self):
        return self._router.trace

    @property
    def websocket(self):
        return self._router.websocket

    @property
    def ws(self):
        "websocket alias"
        return self._router.websocket

    @property
    def options(self):
        return self._router.options

    @property
    def head(self):
        return self._router.head

    def route_handle(
        self,
        endpoint: Callable,
        handle: Callable[[APIRoute], None | APIRoute],
    ):
        for route in self._router.routes:
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

    @staticmethod
    def _on_provider(provider: Provider, route: APIRoute | APIWebSocketRoute):
        if isinstance(route, APIRoute):
            route.responses.update(build_responses(*provider.exceptions))

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
    def _create_class_instance(*, cls: type, **dependencies):
        """创建类实例"""
        instance = cls()
        for k, v in dependencies.items():
            setattr(instance, k, v)

        post_init = getattr(instance, "__post_init__", None)
        if callable(post_init):
            post_init()

        return instance

    @staticmethod
    def _empty_dependency(): ...

    def _create_instance_function(
        self,
        origin: Callable,
        cls: type,
        class_dependencies: Callable,
    ):
        """创建实例函数"""
        cls_dep_name = class_dependencies.__name__

        def _flush_arguments(_args: tuple, kwds: dict):
            kwds.pop("self", None)

        def _create_instance(_args: tuple, kwds: dict):
            dependencies = kwds.pop(cls_dep_name)
            return self._create_class_instance(cls=cls, **dependencies)

        fn = new_function(origin)

        # 把 self 转为类型为空依赖的参数
        # e.g.: (self: Annotated[None, Depends(lambda: None)], ...)
        no_self_arguments = list_parameters(origin)
        no_self_arguments[0] = no_self_arguments[0].replace(
            annotation=Annotated[
                None,
                params.Depends(self._empty_dependency),
            ],
        )
        update_signature(fn, parameters=no_self_arguments)

        inject_parameter(
            fn,
            name=cls_dep_name,
            default=params.Depends(class_dependencies),
        )

        if Is.coroutine_function(origin):

            @wraps(fn)
            async def async_wrapper(*args, **kwds):
                _flush_arguments(args, kwds)
                instance = _create_instance(args, kwds)
                return await origin(instance, *args, **kwds)

            return async_wrapper

        @wraps(fn)
        def wrapper(*args, **kwds):
            _flush_arguments(args, kwds)
            instance = _create_instance(args, kwds)
            return origin(instance, *args, **kwds)

        return wrapper

    def __call__(self, cls: type[T], /) -> type[T]:
        api_routes = [
            (index, i)
            for index, i in enumerate(self._router.routes)
            if isinstance(i, APIRoute | APIWebSocketRoute)
        ]

        for _index, route in api_routes:
            endpoint = route.endpoint
            if hasattr(cls, endpoint.__name__):
                self._router.routes.remove(route)

                if isinstance(endpoint, staticmethod):
                    new_fn = endpoint

                else:
                    class_dependencies = self._create_class_dependencies(cls)
                    for i in analyze_and_update(class_dependencies):
                        responses = {}
                        responses.update(build_responses(*i.exceptions))
                        if i.provider:
                            responses.update(
                                build_responses(*i.provider.exceptions)
                            )
                        if isinstance(route, APIRoute):
                            route.responses.update(responses)
                    new_fn = self._create_instance_function(
                        endpoint, cls, class_dependencies
                    )

                setattr(route, "endpoint", new_fn)

                self._router.routes.append(route)

        self.router.include_router(self._router)
        self._router.routes = []

        return cls
