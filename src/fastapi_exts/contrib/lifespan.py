import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
    asynccontextmanager,
)
from typing import TypeVar

from fastapi import FastAPI


Handler = Callable[
    [FastAPI],
    Awaitable[None] | Coroutine[None, None, None] | None,
]

HandlerT = TypeVar("HandlerT", bound=Handler)

ContextManager = Callable[
    [FastAPI],
    AbstractContextManager | AbstractAsyncContextManager,
]

ContextManagerT = TypeVar("ContextManagerT", bound=ContextManager)


class Lifespan:
    def __init__(self) -> None:
        self.startup_handlers: list[Handler] = []
        self.shutdown_handlers: list[Handler] = []
        self.context_managers: list[ContextManager] = []

    def on_startup(self, fn: HandlerT) -> HandlerT:
        self.startup_handlers.append(fn)
        return fn

    def on_shutdown(self, fn: HandlerT) -> HandlerT:
        self.shutdown_handlers.append(fn)
        return fn

    def on_context(self, fn: ContextManagerT) -> ContextManagerT:
        self.context_managers.append(fn)
        return fn

    def include(self, lifespan: "Lifespan"):
        self.startup_handlers.extend(lifespan.startup_handlers)
        self.shutdown_handlers.extend(lifespan.shutdown_handlers)
        self.context_managers.extend(lifespan.context_managers)

    @asynccontextmanager
    async def __call__(self, _app: FastAPI):
        for hook in self.startup_handlers:
            ret = hook(_app)
            if asyncio.iscoroutine(ret):
                await ret

        async with AsyncExitStack() as stack:
            for ctx in self.context_managers:
                i = ctx(_app)
                if isinstance(i, AbstractContextManager):
                    stack.enter_context(i)
                elif isinstance(i, AbstractAsyncContextManager):
                    await stack.enter_async_context(i)

            yield

        for hook in self.shutdown_handlers:
            ret = hook(_app)
            if asyncio.iscoroutine(ret):
                await ret
