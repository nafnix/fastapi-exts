from abc import ABC
from collections.abc import Mapping
from typing import Any, Generic, Literal, TypeVar, cast

from fastapi import FastAPI, Request, status
from fastapi.responses import Response
from fastapi.utils import is_body_allowed_for_status_code
from pydantic import BaseModel, Field, create_model

from fastapi_exts.contrib.responses import (
    ResponseInfoInterface,
    ResponseInfoSchemaInterface,
)


try:
    import orjson  # type: ignore
except ImportError:
    orjson = None

if orjson is None:
    from fastapi.responses import JSONResponse
else:
    from fastapi.responses import ORJSONResponse as JSONResponse


BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


class BaseHTTPError(ABC, ResponseInfoInterface, Exception):
    status = status.HTTP_400_BAD_REQUEST
    headers = None

    media_type: str


class BaseHTTPDataError(
    BaseHTTPError,
    ABC,
    ResponseInfoSchemaInterface[BaseModelT],
):
    data: BaseModelT


class HTTPCodeError(BaseHTTPDataError[BaseModelT], Generic[BaseModelT]):
    code: str | None = None
    message: str | None = None

    @classmethod
    def get_code(cls):
        return cls.code or cls.__name__

    __get_schema_name__: str | None = None
    __get_schema_kwargs__: Mapping | None = None
    """
    see:
    - https://docs.pydantic.dev/latest/api/base_model/#pydantic.create_model
    - https://docs.pydantic.dev/latest/concepts/models/#dynamic-model-creation
    """

    @classmethod
    def get_schema(cls) -> type[BaseModelT]:
        code = cls.get_code()
        kwargs = {"code": (Literal[code], ...), "message": (str, ...)}
        kwargs.update(cls.__get_schema_kwargs__ or {})

        return cast(
            type[BaseModelT],
            create_model(cls.__get_schema_name__ or cls.__name__, **kwargs),
        )

    def __init__(
        self,
        *,
        message: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {
            "code": self.get_code(),
            "message": message or self.message or "operation failed",
        }

        schema = self.get_schema()
        self.data = schema(**kwargs)

        self.headers = headers or self.headers

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.status}>"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__: str(self.data)}>"


class HTTPProblem(BaseHTTPDataError):  # noqa: N818
    type: str | None = None
    title: str | None = None
    media_type = "application/problem+json"

    """
    see:
    - https://docs.pydantic.dev/latest/api/base_model/#pydantic.create_model
    - https://docs.pydantic.dev/latest/concepts/models/#dynamic-model-creation
    """

    def __init__(
        self,
        *,
        detail: str | None = None,
        instance: str | None = None,
        headers: dict | None = None,
    ) -> None:
        self.detail = detail
        self.instance = instance
        kwds = {
            "title": self.get_title(),
            "status": self.status,
        }
        if self.type is not None:
            kwds["type"] = self.type
        if self.detail is not None:
            kwds["detail"] = self.detail
        if self.instance is not None:
            kwds["instance"] = self.instance

        self.data = self.get_schema().model_validate(kwds)
        self.headers = headers or self.headers

    @classmethod
    def get_title(cls):
        return cls.title or cls.__name__

    __get_schema_name__: str | None = None
    __get_schema_kwargs__: Mapping | None = None

    @classmethod
    def get_schema(cls):
        type_ = cls.type
        status = cls.status
        title = cls.get_title()

        kwargs: dict = {
            "type": (
                str,
                Field(None, json_schema_extra={"format": "uri"}),
            ),
            "title": (Literal[title], ...),
            "status": (Literal[status], ...),
            "detail": (str, None),
            "instance": (
                str,
                Field(None, json_schema_extra={"format": "uri"}),
            ),
        }

        if type_ is not None:
            kwargs["type"] = (
                Literal[type_],
                Field(json_schema_extra={"format": "uri"}),
            )

        kwargs.update(cls.__get_schema_kwargs__ or {})

        name = cls.__name__
        return create_model(cls.__get_schema_name__ or name, **kwargs)


def ext_http_error_handler(_: Request, exc: BaseHTTPError):
    headers = getattr(exc, "headers", None)

    if not is_body_allowed_for_status_code(exc.status):
        return Response(status_code=exc.status, headers=headers)

    data = getattr(exc, "data", None)
    if isinstance(data, BaseModel):
        data = data.model_dump(exclude_unset=True)

    media_type = getattr(exc, "media_type", None)

    return JSONResponse(
        data,
        status_code=exc.status,
        headers=headers,
        media_type=media_type,
    )


class ExceptionExtension:
    def setup(self, app: FastAPI):
        app.exception_handlers[BaseHTTPError] = ext_http_error_handler
