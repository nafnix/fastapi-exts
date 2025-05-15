import inspect
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from functools import partial, wraps
from string import Template
from typing import Annotated, Any, Generic, Self, TypeVar, overload

from fastapi.params import Depends

from fastapi_exts._utils import (
    Is,
    get_annotated_metadata,
    get_annotated_type,
    list_parameters,
    update_signature,
    with_parameter,
)

from ._types import ContextT, EndpointT, ExceptionT, MessageTemplate, P, T
from .context import (
    AnyLogRecordContextT,
    LogRecordContextT,
)
from .models import (
    LogRecordFailureDetail,
    LogRecordFailureSummary,
    LogRecordSuccessDetail,
    LogRecordSuccessSummary,
)
from .utils import (
    async_execute,
    is_failure,
    is_success,
    sync_execute,
)


SuccessDetailT = TypeVar("SuccessDetailT", bound=LogRecordSuccessDetail)
FailureDetailT = TypeVar("FailureDetailT", bound=LogRecordFailureDetail)


class Handler(Generic[SuccessDetailT, FailureDetailT, P]):
    def before(self, *args: P.args, **kwds: P.kwargs): ...
    def after(
        self,
        detail: SuccessDetailT | FailureDetailT,
        *args: P.args,
        **kwds: P.kwargs,
    ): ...

    def success(
        self,
        detail: SuccessDetailT,
        *args: P.args,
        **kwds: P.kwargs,
    ): ...
    def failure(
        self,
        detail: FailureDetailT,
        *args: P.args,
        **kwds: P.kwargs,
    ): ...


class AsyncHandler(Generic[SuccessDetailT, FailureDetailT, P]):
    async def before(self, *args: P.args, **kwds: P.kwargs): ...
    async def after(
        self,
        detail: SuccessDetailT | FailureDetailT,
        *args: P.args,
        **kwds: P.kwargs,
    ): ...

    async def success(
        self,
        detail: SuccessDetailT,
        *args: P.args,
        **kwds: P.kwargs,
    ): ...
    async def failure(
        self,
        detail: FailureDetailT,
        *args: P.args,
        **kwds: P.kwargs,
    ): ...


_HandlerT = TypeVar("_HandlerT", bound=Handler | AsyncHandler)

_SuccessHandlerT = TypeVar("_SuccessHandlerT", bound=Callable)
_FailureHandlerT = TypeVar("_FailureHandlerT", bound=Callable)
_UtilFunctionT = TypeVar("_UtilFunctionT", bound=Callable)


class _AbstractLogRecord(
    ABC,
    Generic[
        _HandlerT,
        _SuccessHandlerT,
        _FailureHandlerT,
        AnyLogRecordContextT,
        EndpointT,
        _UtilFunctionT,
    ],
):
    _log_record_deps_name = "__log_record_dependencies"

    def __init__(
        self,
        *,
        success: MessageTemplate | None = None,
        failure: MessageTemplate | None = None,
        functions: list[_UtilFunctionT]
        | dict[str, _UtilFunctionT]
        | None = None,
        dependencies: list[Depends] | dict[str, Depends] | None = None,
        context_factory: Callable[[], AnyLogRecordContextT] | None = None,
        handlers: list[_HandlerT] | None = None,
        success_handlers: list[_SuccessHandlerT] | None = None,
        failure_handlers: list[_FailureHandlerT] | None = None,
        **extra,
    ) -> None:
        self.success = success or ""
        self.failure = failure or ""

        self.dependencies: dict[str, Depends] = {}

        self.context_factory = context_factory

        self.functions: dict[str, _UtilFunctionT] = {}

        self.handlers = handlers or []
        self.success_handlers = success_handlers or []
        self.failure_handlers = failure_handlers or []

        # 用于判断当前装饰的是哪个端点
        self._endpoints: dict[Callable, EndpointT] = {}

        # self._ignore_first =

        if dependencies:
            if isinstance(dependencies, dict):
                for name, dep in dependencies.items():
                    self.add_dependency(dep, name)
            else:
                for dep in dependencies:
                    self.add_dependency(dep)

        if functions:
            if isinstance(functions, dict):
                for name, fn in functions.items():
                    self.register_function(fn, name)
            else:
                for fn in functions:
                    self.register_function(fn)
        self.extra = extra

    @overload
    def register_function(self, fn: _UtilFunctionT): ...
    @overload
    def register_function(self, fn: _UtilFunctionT, name: str): ...
    def register_function(self, fn: _UtilFunctionT, name: str | None = None):
        self.functions[name or fn.__name__] = fn

    def description(self) -> str | None: ...

    @overload
    def add_dependency(self, dependency: Depends): ...
    @overload
    def add_dependency(self, dependency: Depends, name: str): ...
    def add_dependency(self, dependency: Depends, name: str | None = None):
        assert callable(dependency.dependency), (
            "The dependency must be a callable function"
        )
        name = name or (
            dependency.dependency and dependency.dependency.__name__
        )

        if name in self.dependencies:
            msg = f"The dependency name {name} is already in use"
            raise ValueError(msg)

        self.dependencies.setdefault(name, dependency)

    def add_handler(self, handler: _HandlerT, /):
        self.handlers.append(handler)

    def add_success_handler(self, handler: _SuccessHandlerT, /):
        self.success_handlers.append(handler)

    def add_failure_handler(self, handler: _FailureHandlerT, /):
        self.failure_handlers.append(handler)

    @abstractmethod
    def _log_function(self, fn: Callable, endpoint: EndpointT) -> Callable: ...

    def _log_record_deps(self, endpoint: EndpointT):
        """创建日志所需依赖

        :param endpoint: 当日志所需依赖报错时, 导致依赖报错的端点
        :return: 日志所需依赖
        """

        if not self.dependencies:
            return None

        def log_record_dependencies(**kwargs):
            return kwargs

        parameters = []
        for name, dep in self.dependencies.items():
            assert dep.dependency is not None

            parameters.append(
                inspect.Parameter(
                    name=name,
                    kind=inspect.Parameter.KEYWORD_ONLY,
                    default=Depends(
                        self._log_function(dep.dependency, endpoint),
                        use_cache=dep.use_cache,
                    ),
                )
            )

        update_signature(log_record_dependencies, parameters=parameters)

        return log_record_dependencies

    def _with_log_record_deps(self, call: Callable, endpoint: EndpointT):
        # 日志记录器本身所需的依赖
        log_record_deps = self._log_record_deps(endpoint)

        if callable(log_record_deps):
            old = call
            new = wraps(old)(partial(call))
            parameters, *_ = with_parameter(
                new,
                name=self._log_record_deps_name,
                default=Depends(log_record_deps, use_cache=True),
            )
            update_signature(new, parameters=parameters)
            return new
        return call

    def _wrap_dependency(
        self, parameter: inspect.Parameter, endpoint: EndpointT
    ):
        default = parameter.default
        annotation = parameter.annotation
        with_log_record_deps_dep = partial(
            self._with_log_record_deps, endpoint=endpoint
        )
        # e.g.
        # 1. def endpoint(value=Depends(dependency_function)): ...
        # 2. >>>>>>
        #    class Value:
        #        def __init__(self, demo: int):
        #            self.demo = demo
        #
        #    def endpoint(value: Value = Depends()): ...
        #    <<<<<<
        if isinstance(default, Depends):
            # handle 1
            if default.dependency:
                new_depend = with_log_record_deps_dep(default.dependency)
                new_dep = Depends(
                    self._log_function(new_depend, endpoint),
                    use_cache=default.use_cache,
                )
                return parameter.replace(default=new_dep)
            # handle 2
            if inspect.isclass(annotation):
                cls = with_log_record_deps_dep(annotation)
                return parameter.replace(
                    annotation=self._log_function(cls, endpoint)
                )

        # e.g.
        # 1. >>>>>>
        #    class Value:
        #        def __init__(self, demo: int):
        #            self.demo = demo
        #
        #    def endpoint(value: Annotated[Value, Depends()]): ...
        #    <<<<<<
        #
        # 2. >>>>>>
        #    def endpoint(value: Annotated[Value, Depends(dependency_function)]): ...  # noqa: E501, W505
        #    <<<<<<
        elif Is.annotated(annotation):
            typ = get_annotated_type(annotation)
            metadata = []
            cls_dep = True
            for i in get_annotated_metadata(annotation):
                if isinstance(i, Depends):
                    if i.dependency:
                        new_depend = with_log_record_deps_dep(i.dependency)

                        cls_dep = False
                        new_dep = Depends(
                            self._log_function(new_depend, endpoint),
                            use_cache=default.use_cache,
                        )
                        metadata.append(new_dep)
                    else:
                        metadata.append(i)
                else:
                    metadata.append(i)

            if cls_dep and inspect.isclass(typ):
                typ = self._log_function(
                    with_log_record_deps_dep(typ),
                    endpoint,
                )

            return parameter.replace(annotation=Annotated[typ, *metadata])

        return parameter

    @classmethod
    def new(  # noqa: PLR0913
        cls,
        *,
        old: Self,  # noqa: ARG003
        success: MessageTemplate | None = None,
        failure: MessageTemplate | None = None,
        functions: list[_UtilFunctionT]
        | dict[str, _UtilFunctionT]
        | None = None,
        dependencies: list[Depends] | dict[str, Depends] | None = None,
        context_factory: Callable[[], AnyLogRecordContextT] | None = None,
        handlers: list[_HandlerT] | None = None,
        success_handlers: list[_SuccessHandlerT] | None = None,
        failure_handlers: list[_FailureHandlerT] | None = None,
        **extra,
    ) -> Self:
        return cls(
            success=success,
            failure=failure,
            functions=functions,
            dependencies=dependencies,
            context_factory=context_factory,
            handlers=handlers,
            success_handlers=success_handlers,
            failure_handlers=failure_handlers,
            **extra,
        )

    @overload
    def __call__(self, endpoint: EndpointT) -> EndpointT: ...

    @overload
    def __call__(
        self,
        *,
        success: MessageTemplate | None = None,
        failure: MessageTemplate | None = None,
        functions: list[_UtilFunctionT]
        | dict[str, _UtilFunctionT]
        | None = None,
        dependencies: list[Depends] | dict[str, Depends] | None = None,
        context_factory: Callable[[], AnyLogRecordContextT] | None = None,
        handlers: list[_HandlerT] | None = None,
        success_handlers: list[_SuccessHandlerT] | None = None,
        failure_handlers: list[_FailureHandlerT] | None = None,
        **extra,
    ) -> Callable[[EndpointT], EndpointT]: ...

    def __call__(  # noqa: PLR0913
        self,
        endpoint: EndpointT | None = None,
        *,
        success: MessageTemplate | None = None,
        failure: MessageTemplate | None = None,
        functions: list[_UtilFunctionT]
        | dict[str, _UtilFunctionT]
        | None = None,
        dependencies: list[Depends] | dict[str, Depends] | None = None,
        context_factory: Callable[[], AnyLogRecordContextT] | None = None,
        handlers: list[_HandlerT] | None = None,
        success_handlers: list[_SuccessHandlerT] | None = None,
        failure_handlers: list[_FailureHandlerT] | None = None,
        **extra,
    ):
        if endpoint is None:
            return self.new(
                old=self,
                success=success,
                failure=failure,
                functions=functions,
                dependencies=dependencies,
                context_factory=context_factory,
                handlers=handlers,
                success_handlers=success_handlers,
                failure_handlers=failure_handlers,
                **extra,
            )

        ofn = endpoint

        # 日志记录器本身所需的依赖
        parameters = [
            self._wrap_dependency(p, endpoint)
            for p in list_parameters(endpoint)
        ]
        new_fn = wraps(endpoint)(partial(endpoint))
        update_signature(new_fn, parameters=parameters)

        # 日志记录器本身所需的依赖
        new_fn = self._with_log_record_deps(new_fn, endpoint)

        self._endpoints[new_fn] = ofn

        return self._log_function(new_fn, endpoint)

    @abstractmethod
    def _execute_before_handles(self, args: tuple, kwds: dict, /):
        raise NotImplementedError

    @abstractmethod
    def _execute(self, fn: Callable, args: tuple, kwds: dict, /):
        raise NotImplementedError


class AbstractLogRecord(
    _AbstractLogRecord[
        Handler[SuccessDetailT, FailureDetailT, P],
        Callable[[SuccessDetailT], None],
        Callable[[FailureDetailT], None],
        LogRecordContextT,
        EndpointT,
        Callable[P, Any],
    ],
    ABC,
    Generic[
        SuccessDetailT,
        FailureDetailT,
        P,
        T,
        ExceptionT,
        LogRecordContextT,
        ContextT,
        EndpointT,
    ],
):
    @overload
    def format_message(
        self,
        summary: LogRecordSuccessSummary[T],
        extra: dict[str, Any] | None = None,
        context: ContextT | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> str: ...
    @overload
    def format_message(
        self,
        summary: LogRecordFailureSummary[ExceptionT],
        extra: dict[str, Any] | None = None,
        context: ContextT | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> str: ...
    def format_message(
        self,
        summary: LogRecordSuccessSummary[T]
        | LogRecordFailureSummary[ExceptionT],
        extra: dict[str, Any] | None = None,
        context: ContextT | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> str:
        kwargs["$"] = {
            "summary": summary,
            "context": context,
            "extra": extra,
        }

        message = self.success if summary.success else self.failure

        result_ = ""

        if isinstance(message, str):
            result_ += message.format(*args, **kwargs)

        elif isinstance(message, Template):
            identifiers = message.get_identifiers()
            values = {}
            for i in identifiers:
                fn = self.functions.get(i)
                if fn:
                    values[i] = fn(*args, **kwargs)

            result_ += message.safe_substitute(
                **values,
                **kwargs,
            ).format(*args, **kwargs)

        return result_

    @abstractmethod
    def get_success_detail(
        self,
        *,
        summary: LogRecordSuccessSummary[T],
        message: str,
        context: ContextT | None,
        endpoint: EndpointT,
        extra: dict[str, Any] | None,
    ) -> SuccessDetailT:
        raise NotImplementedError

    @abstractmethod
    def get_failure_detail(
        self,
        *,
        summary: LogRecordFailureSummary,
        message: str,
        context: ContextT | None,
        endpoint: EndpointT,
        extra: dict[str, Any] | None,
    ) -> FailureDetailT:
        raise NotImplementedError

    def _execute_before_handles(self, args: tuple, kwds: dict, /):
        for i in self.handlers:
            i.before(*args, **kwds)

    def _execute(self, fn: Callable, args: tuple, kwds: dict, /):
        context = None
        if self.context_factory:
            with self.context_factory() as ctx:
                summary = sync_execute(fn, *args, **kwds)
            context = ctx.info
        else:
            summary = sync_execute(fn, *args, **kwds)
        return summary, context

    def _log_function(self, fn: Callable, endpoint: EndpointT):
        @wraps(fn)
        def decorator(*args, **kwds):
            is_endpoint_fn = fn in self._endpoints

            log_record_deps = kwds.pop(self._log_record_deps_name, None)
            context: ContextT | None = None

            if is_endpoint_fn:
                self._execute_before_handles(args, kwds)

                summary, context = self._execute(fn, args, kwds)
            else:
                summary = sync_execute(fn, *args, **kwds)

            if is_endpoint_fn and is_success(summary):
                message = self.format_message(
                    summary,
                    log_record_deps,
                    context,
                    *args,
                    **kwds,
                )
                detail = self.get_success_detail(
                    summary=summary,
                    context=context,
                    message=message,
                    endpoint=endpoint,
                    extra=log_record_deps,
                )

                for i in self.success_handlers:
                    i(detail)

                for i in self.handlers:
                    i.success(detail, *args, **kwds)
                    i.after(detail, *args, **kwds)

                return summary.result

            if is_failure(summary):
                # 失败时, 依赖的上下文有可能是空的(例如如果是依赖项异常, 那么上下文是空的)  # noqa: E501, W505
                # 如果是端点本身的异常, 则可能有值(具体看端点有没有触发上下文操作) # noqa: E501, W505
                message = self.format_message(
                    summary,
                    log_record_deps,
                    context,
                    *args,
                    **kwds,
                )
                detail = self.get_failure_detail(
                    summary=summary,
                    context=context,
                    message=message,
                    endpoint=endpoint,
                    extra=log_record_deps,
                )

                for i in self.failure_handlers:
                    i(detail)

                for i in self.handlers:
                    i.failure(detail, *args, **kwds)
                    i.after(detail, *args, **kwds)

                raise summary.exception

            return summary.result

        return decorator


class AbstractAsyncLogRecord(
    _AbstractLogRecord[
        Handler[SuccessDetailT, FailureDetailT, P]
        | AsyncHandler[SuccessDetailT, FailureDetailT, P],
        Callable[[SuccessDetailT], None | Awaitable[None]],
        Callable[[FailureDetailT], None | Awaitable[None]],
        AnyLogRecordContextT,
        EndpointT,
        Callable[P, Awaitable | Any],
    ],
    ABC,
    Generic[
        SuccessDetailT,
        FailureDetailT,
        P,
        T,
        ExceptionT,
        AnyLogRecordContextT,
        ContextT,
        EndpointT,
    ],
):
    @overload
    async def format_message(
        self,
        summary: LogRecordSuccessSummary[T],
        extra: dict[str, Any] | None = None,
        context: ContextT | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> str: ...
    @overload
    async def format_message(
        self,
        summary: LogRecordFailureSummary[ExceptionT],
        extra: dict[str, Any] | None = None,
        context: ContextT | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> str: ...
    async def format_message(
        self,
        summary: LogRecordSuccessSummary[T]
        | LogRecordFailureSummary[ExceptionT],
        extra: dict[str, Any] | None = None,
        context: ContextT | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> str:
        kwargs["$"] = {
            "summary": summary,
            "context": context,
            "extra": extra,
        }

        message = self.success if summary.success else self.failure

        result_ = ""

        if isinstance(message, str):
            result_ += message.format(*args, **kwargs)

        elif isinstance(message, Template):
            identifiers = message.get_identifiers()
            values = {}
            for i in identifiers:
                fn = self.functions.get(i)
                if fn:
                    fn_result = fn(*args, **kwargs)
                    if Is.awaitable(fn_result):
                        fn_result = await fn_result
                    values[i] = fn_result

            result_ += message.safe_substitute(
                **values,
                **kwargs,
            ).format(*args, **kwargs)

        return result_

    @abstractmethod
    async def get_success_detail(
        self,
        *,
        summary: LogRecordSuccessSummary[T],
        message: str,
        context: ContextT | None,
        endpoint: EndpointT,
        extra: dict[str, Any] | None,
    ) -> SuccessDetailT:
        raise NotImplementedError

    @abstractmethod
    async def get_failure_detail(
        self,
        *,
        summary: LogRecordFailureSummary,
        message: str,
        context: ContextT | None,
        endpoint: EndpointT,
        extra: dict[str, Any] | None,
    ) -> FailureDetailT:
        raise NotImplementedError

    async def _execute_before_handles(self, args: tuple, kwds: dict, /):
        for i in self.handlers:
            _ = i.before(*args, **kwds)
            if Is.awaitable(_):
                await _

    async def _execute(self, fn: Callable, args: tuple, kwds: dict, /):
        context = None
        if self.context_factory:
            context_ = self.context_factory()
            if Is.async_context(context_):
                async with context_ as ctx:
                    summary = await async_execute(fn, *args, **kwds)
                context = ctx.info
            else:
                assert Is.context(context_)
                with context_ as ctx:
                    summary = await async_execute(fn, *args, **kwds)
                context = ctx.info
        else:
            summary = await async_execute(fn, *args, **kwds)
        return summary, context

    async def _execute_success_handlers(self, detail):
        for i in self.success_handlers:
            i_result = i(detail)
            if Is.awaitable(i_result):
                await i_result

    async def _execute_failure_handlers(self, detail):
        for i in self.failure_handlers:
            i_result = i(detail)
            if Is.awaitable(i_result):
                await i_result

    async def _execute_after_handlers(
        self,
        detail,
        args: tuple,
        kwds: dict,
        success: bool,  # noqa: FBT001
    ):
        for i in self.handlers:
            if success:
                _ = i.success(detail, *args, **kwds)
                if Is.awaitable(_):
                    await _
            else:
                _ = i.failure(detail, *args, **kwds)
                if Is.awaitable(_):
                    await _

            _ = i.after(detail, *args, **kwds)
            if Is.awaitable(_):
                await _

    def _log_function(self, fn: Callable, endpoint: EndpointT):
        @wraps(fn)
        async def decorator(*args, **kwds):
            is_endpoint_fn = fn in self._endpoints

            log_record_deps: dict[str, Any] | None = kwds.pop(
                self._log_record_deps_name, None
            )
            context: ContextT | None = None

            if is_endpoint_fn:
                await self._execute_before_handles(args, kwds)

                # kwds.setdefault(self._endpoint_deps_name, None)
                # args, kwds = self._get_arguments(args, kwds)
                summary, context = await self._execute(fn, args, kwds)

            else:
                summary = await async_execute(fn, *args, **kwds)

            if is_endpoint_fn and is_success(summary):
                message = await self.format_message(
                    summary,
                    log_record_deps,
                    context,
                    *args,
                    **kwds,
                )
                detail = await self.get_success_detail(
                    summary=summary,
                    context=context,
                    message=message,
                    endpoint=endpoint,
                    extra=log_record_deps,
                )

                await self._execute_success_handlers(detail)
                await self._execute_after_handlers(detail, args, kwds, True)  # noqa: FBT003

                return summary.result

            if is_failure(summary):
                # 失败时, 依赖的上下文有可能是空的(例如如果是依赖项异常, 那么上下文是空的) # noqa: E501, W505
                # 如果是端点本身的异常, 则可能有值(具体看端点有没有触发上下文操作) # noqa: E501, W505
                message = await self.format_message(
                    summary,
                    log_record_deps,
                    context,
                    *args,
                    **kwds,
                )
                detail = await self.get_failure_detail(
                    summary=summary,
                    context=context,
                    message=message,
                    endpoint=endpoint,
                    extra=log_record_deps,
                )

                await self._execute_failure_handlers(detail)
                await self._execute_after_handlers(detail, args, kwds, False)  # noqa: FBT003

                raise summary.exception

            return summary.result

        return decorator
