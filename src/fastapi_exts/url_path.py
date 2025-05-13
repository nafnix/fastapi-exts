import re
from typing import Self, overload

from typing_extensions import Buffer


_replace_pattern = re.compile(r"^(?:\/)+|(?:\/)+$")


def _transform(value):
    return _replace_pattern.sub("", value)


class URLPath(str):
    __slots__ = ()

    @staticmethod
    def _initial(seq: str):
        return f"/{_transform(seq)}"

    @overload
    def __new__(cls, object: object = ...): ...
    @overload
    def __new__(
        cls,
        object: Buffer,
        encoding: str = ...,
        errors: str = ...,
    ): ...
    def __new__(cls, object: object | Buffer = ..., *args, **kwds) -> Self:  # noqa: A002
        string = str(object, *args, **kwds)
        return super().__new__(cls, cls._initial(string))

    def __truediv__(self, other: Self | str | int):
        args: list[str] = [self]
        if not isinstance(other, str):
            args.append(str(other))
        else:
            args.append(other)

        path = "/".join([_transform(arg) for arg in args])

        return URLPath(path)
