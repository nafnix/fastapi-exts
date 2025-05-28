import re
from enum import StrEnum, auto
from typing import Literal


UpperMethodLiteral = Literal[
    "GET",
    "POST",
    "PATCH",
    "PUT",
    "DELETE",
    "OPTIONS",
    "HEAD",
    "TRACE",
]


LowerMethodLiteral = Literal[
    "get",
    "post",
    "patch",
    "put",
    "delete",
    "options",
    "head",
    "trace",
]


class Methods(StrEnum):
    GET = auto()
    POST = auto()
    PATCH = auto()
    PUT = auto()
    DELETE = auto()
    OPTIONS = auto()
    HEAD = auto()
    TRACE = auto()


RequestMethod = Methods | LowerMethodLiteral | UpperMethodLiteral

METHOD_PATTERNS = {
    method: re.compile(f"^{method}", re.IGNORECASE) for method in Methods
}
