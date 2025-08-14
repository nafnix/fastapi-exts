from collections.abc import Mapping
from typing import Literal

from pydantic import Field, create_model

from .base import BaseHTTPDataError


class HTTPProblem(BaseHTTPDataError):
    type: str | None = None
    title: str | None = None
    media_type = "application/problem+json"
    detail: str | None = None

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
        self.detail = detail or self.detail
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
