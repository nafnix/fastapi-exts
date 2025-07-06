from abc import ABC
from collections.abc import Iterable, Mapping
from typing import Any, Generic, Literal, cast

from fastapi import status
from fastapi.responses import JSONResponse, ORJSONResponse, Response
from fastapi.utils import is_body_allowed_for_status_code
from pydantic import BaseModel, create_model

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


def ext_http_error_handler(_, exc: BaseHTTPError):
    headers = exc.headers

    if not is_body_allowed_for_status_code(exc.status):
        return Response(status_code=exc.status, headers=headers)

    if isinstance(exc.data, BaseModel):
        content = exc.data.model_dump(exclude_none=True)
    else:
        content = exc.data

    if orjson:
        return ORJSONResponse(
            content,
            status_code=exc.status,
            headers=headers,
        )

    return JSONResponse(
        content,
        status_code=exc.status,
        headers=headers,
    )
