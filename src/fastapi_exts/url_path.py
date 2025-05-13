import re
from collections import UserString
from typing import Self


class URLPath(UserString):
    _replace_pattern = re.compile(r"^(?:\/)+|(?:\/)+$")

    def _validation(self, value: str) -> str:
        return self._replace_pattern.sub("", value)

    def __init__(self, seq: str | int | None = None) -> None:
        if seq is None:
            seq = ""

        seq = self._validation(seq) if isinstance(seq, str) else f"{seq}"
        seq = f"/{seq}"

        super().__init__(seq)

    def __truediv__(self, other: Self | str | int):
        args: list[str] = [self.data]
        if not isinstance(other, str):
            args.append(str(other))
        else:
            args.append(other)

        path = "/".join([self._validation(arg) for arg in args])

        return URLPath(path)
