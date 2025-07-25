import re
from typing import Self, overload

from typing_extensions import Buffer


class Path(str):
    __slots__ = ()
    __separator__ = "/"
    __prefix__ = ""
    __startswith_separator__ = True

    @classmethod
    def _init_pattern(cls):
        separator = re.escape(cls.__separator__)
        prefix = re.escape(cls.__prefix__)
        cls.__pattern__ = re.compile(
            f"^(?:{separator}|{prefix})+|(?:{separator})+$"
            if cls.__prefix__
            else f"^(?:{separator})+|(?:{separator})+$"
        )

    def __init_subclass__(cls) -> None:
        cls._init_pattern()

    @classmethod
    def _replace(cls, value: str):
        if not hasattr(cls, "__pattern__"):
            cls._init_pattern()

        return cls.__pattern__.sub("", value)

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
        result = cls._replace(string)

        if cls.__prefix__:
            result = cls.__separator__.join([cls.__prefix__, result])

        if cls.__startswith_separator__:
            result = f"{cls.__separator__}{result}"

        return super().__new__(cls, result)

    def __truediv__(self, other: Self | str | int):
        args: list[str] = [self]
        if not isinstance(other, str):
            args.append(str(other))
        else:
            args.append(other)

        path = self.__separator__.join([self._replace(arg) for arg in args])

        return self.__class__(path)

    @property
    def parent(self):
        return self.__class__(
            self.__separator__.join(self.split(self.__separator__)[:-1])
        )
