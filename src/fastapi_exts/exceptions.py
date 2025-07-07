from abc import ABC
from collections.abc import Iterable, Mapping
from typing import Any, Generic, Literal, cast

from fastapi import status
from fastapi.responses import Response
from fastapi.utils import is_body_allowed_for_status_code
from pydantic import BaseModel, Field, create_model


try:
    import orjson
except ImportError:
    orjson = None

if orjson is None:
    from fastapi.responses import JSONResponse
else:
    from fastapi.responses import ORJSONResponse as JSONResponse


from .interfaces import (
    BaseModelT_co,
    HTTPErrorInterface,
    HTTPSchemaErrorInterface,
)


try:
    import orjson  # type: ignore
except ModuleNotFoundError:  # pragma: nocover
    orjson = None


class BaseHTTPError(Exception, ABC, HTTPErrorInterface):
    status = status.HTTP_400_BAD_REQUEST
    headers = None

    data: Any = None


class BaseHTTPDataError(
    BaseHTTPError,
    ABC,
    HTTPSchemaErrorInterface[BaseModelT_co],
):
    data: BaseModelT_co


class NamedHTTPError(
    BaseHTTPDataError[BaseModelT_co],
    Generic[BaseModelT_co],
):
    code: str | None = None
    message: str | None = None

    targets: Iterable[str] | None = None

    __schema_name__: str | None = None
    __build_schema_kwargs__: Mapping | None = None
    """
    see:
    - https://docs.pydantic.dev/latest/api/base_model/#pydantic.create_model
    - https://docs.pydantic.dev/latest/concepts/models/#dynamic-model-creation
    """

    @classmethod
    def get_code(cls):
        return cls.code or cls.__name__.removesuffix("Error")

    @classmethod
    def build_schema(cls) -> type[BaseModelT_co]:
        code = cls.get_code()
        kwargs = {
            "code": (Literal[code], ...),
            "message": (str, ...),
        }
        if cls.targets is not None:
            kwargs["target"] = (Literal[*cls.targets], ...)

        kwargs.update(cls.__build_schema_kwargs__ or {})

        return cast(
            type[BaseModelT_co],
            create_model(cls.__schema_name__ or f"{code}Model", **kwargs),
        )

    def __init__(
        self,
        *,
        message: str | None = None,
        target: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {
            "code": self.get_code(),
            "message": message or self.message or "operation failed",
        }

        if target:
            kwargs["target"] = target
            kwargs["message"] = kwargs["message"].format(target=target)

        schema = self.build_schema()

        self.data = schema(**kwargs)

        self.headers = headers or self.headers

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.status}>"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__: str(self.data)}>"


class HTTPProblem(BaseHTTPDataError):  # noqa: N818
    type: str | None = None

    title: str

    __schema_name__: str | None = None
    __build_schema_kwargs__: Mapping | None = None
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
    ) -> None:
        self.detail = detail
        self.instance = instance
        kwds = {
            "title": self.title,
            "status": self.status,
        }
        if self.type:
            kwds["type"] = self.type
        if self.detail:
            kwds["detail"] = self.detail
        if self.instance:
            kwds["instance"] = self.instance

        self.data = self.build_schema().model_validate(kwds)

    @classmethod
    def build_schema(cls):
        type_ = cls.type
        status = cls.status

        kwargs: dict = {
            "type": (
                str,
                Field(None, json_schema_extra={"format": "uri"}),
            ),
            "title": (Literal[cls.title], ...),
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

        kwargs.update(cls.__build_schema_kwargs__ or {})

        name = cls.__name__
        return create_model(cls.__schema_name__ or name, **kwargs)


def ext_http_error_handler(_, exc: BaseHTTPError):
    headers = exc.headers

    if not is_body_allowed_for_status_code(exc.status):
        return Response(status_code=exc.status, headers=headers)

    if isinstance(exc.data, BaseModel):
        content = exc.data.model_dump(exclude_none=True)
    else:
        content = exc.data

    media_type = None
    if isinstance(exc, HTTPProblem):
        media_type = "application/problem+json"

    return JSONResponse(
        content,
        status_code=exc.status,
        headers=headers,
        media_type=media_type,
    )
