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


Hook = Callable[
    [FastAPI],
    Awaitable[None] | Coroutine[None, None, None] | None,
]

HookT = TypeVar("HookT", bound=Hook)

ContextManager = Callable[
    [FastAPI],
    AbstractContextManager | AbstractAsyncContextManager,
]

ContextManagerT = TypeVar("ContextManagerT", bound=ContextManager)


class Lifespan:
    def __init__(self) -> None:
        self._startup_hooks: list[Hook] = []
        self._shutdown_hooks: list[Hook] = []
        self._context_managers: list[ContextManager] = []

    def on_startup(self, fn: HookT) -> HookT:
        self._startup_hooks.append(fn)
        return fn

    def on_shutdown(self, fn: HookT) -> HookT:
        self._shutdown_hooks.append(fn)
        return fn

    def on_context(self, fn: ContextManagerT) -> ContextManagerT:
        self._context_managers.append(fn)
        return fn

    @asynccontextmanager
    async def __call__(self, _app: FastAPI):
        for hook in self._startup_hooks:
            ret = hook(_app)
            if asyncio.iscoroutine(ret):
                await ret

        async with AsyncExitStack() as stack:
            for ctx in self._context_managers:
                i = ctx(_app)
                if isinstance(i, AbstractContextManager):
                    stack.enter_context(i)
                elif isinstance(i, AbstractAsyncContextManager):
                    await stack.enter_async_context(i)

            yield

        for hook in self._shutdown_hooks:
            ret = hook(_app)
            if asyncio.iscoroutine(ret):
                await ret
