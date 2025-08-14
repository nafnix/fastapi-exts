from collections.abc import Mapping
from typing import Any, Generic, Literal, cast

from pydantic import create_model

from .base import BaseHTTPDataError, BaseModelT


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
        kwargs = {
            "code": (Literal[code], ...),
            "message": (str, ...),
        }
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
