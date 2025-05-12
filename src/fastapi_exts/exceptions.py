import inspect
from collections.abc import Callable, Sequence
from typing import Any, Generic, Literal, TypeVar, cast

from fastapi import status
from fastapi.responses import JSONResponse, ORJSONResponse, Response
from fastapi.utils import is_body_allowed_for_status_code
from pydantic import BaseModel, create_model


try:
    import orjson  # type: ignore
except ImportError:  # pragma: nocover
    orjson = None  # type: ignore

BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


class WrapperError(BaseModel, Generic[BaseModelT]):
    @classmethod
    def create(
        cls: type["WrapperError[BaseModelT]"],
        model: BaseModelT,
    ) -> "WrapperError[BaseModelT]":
        raise NotImplementedError


WrapperErrorT = TypeVar("WrapperErrorT", bound=WrapperError)


class NamedHTTPError(Exception, Generic[WrapperErrorT, BaseModelT]):
    status: int = status.HTTP_400_BAD_REQUEST
    code: str | None = None
    targets: Sequence[Any] | None = None
    target_transform: Callable[[Any], Any] | None = None
    message: str | None = None
    wrapper: (
        type[WrapperError[BaseModelT]]
        | tuple[WrapperErrorT, Callable[[BaseModelT], WrapperErrorT]]
        | None
    ) = None

    @classmethod
    def error_name(cls):
        return cls.__name__.removesuffix("Error")

    @classmethod
    def model_class(cls) -> type[BaseModelT]:
        type_ = cls.error_name()
        error_code = cls.code or type_
        kwargs = {
            "code": (Literal[error_code], ...),
            "message": (Literal[cls.message] if cls.message else str, ...),
        }
        if cls.targets:
            kwargs["target"] = (Literal[*cls.transformed_targets()], ...)

        return cast(type[BaseModelT], create_model(f"{type_}Model", **kwargs))

    @classmethod
    def error_code(cls):
        return cls.code or cls.error_name()

    @classmethod
    def transformed_targets(cls) -> list[str]:
        if cls.targets:
            result = []
            for i in cls.targets:
                if cls.target_transform:
                    result.append(cls.target_transform(i))
                else:
                    result.append(i)
            return result
        return []

    def __init__(
        self,
        *,
        message: str | None = None,
        target: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {
            "code": self.error_code(),
            "message": message or self.message or "operation failed",
        }

        if target:
            if self.target_transform:
                target = self.target_transform(target)
            kwargs["target"] = target
            kwargs["message"] = kwargs["message"].format(target=target)

        self.model = self.model_class()(**kwargs)
        create: Callable[[BaseModelT], BaseModel] | None = None
        if inspect.isclass(self.wrapper):
            create = self.wrapper.create
        elif isinstance(self.wrapper, tuple):
            create = self.wrapper[1]
        self.data: BaseModel = (
            create(self.model) if create is not None else self.model
        )

        self.headers = headers

    def __str__(self) -> str:
        return f"{self.status}: {self.data.error.code}"  # type: ignore

    def __repr__(self) -> str:
        return f"{self.model_class: str(self.error)}"

    @classmethod
    def response_class(cls):
        model = cls.model_class()

        if cls.wrapper:
            wrapper: Any
            if inspect.isclass(cls.wrapper):
                wrapper = cls.wrapper
            else:
                wrapper = cls.wrapper[0]
            return wrapper[model]

        return model

    @classmethod
    def response_schema(cls):
        return {cls.status: {"model": cls.response_class()}}


def named_http_error_handler(_, exc: NamedHTTPError):
    headers = exc.headers

    if not is_body_allowed_for_status_code(exc.status):
        return Response(status_code=exc.status, headers=headers)

    if orjson:
        return ORJSONResponse(
            exc.data.model_dump(exclude_none=True),
            status_code=exc.status,
            headers=headers,
        )

    return JSONResponse(
        exc.data.model_dump(exclude_none=True),
        status_code=exc.status,
        headers=headers,
    )


class EndpointError(WrapperError[BaseModelT], Generic[BaseModelT]):
    error: BaseModelT

    @classmethod
    def create(cls, model: BaseModelT):
        return cls(error=model)
