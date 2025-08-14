from datetime import UTC, datetime
from typing import Any, cast


class _Undefined: ...


undefined = cast(Any, _Undefined)


def naive_datetime(dt: datetime):
    return dt.replace(tzinfo=None)


def utc_datetime(dt: datetime):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
