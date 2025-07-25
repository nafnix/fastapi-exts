from typing import TYPE_CHECKING

from .context import correlation_id_var


if TYPE_CHECKING:
    from logging import LogRecord


def _trim_string(string: str | None, string_length: int | None) -> str | None:
    return (
        string[:string_length]
        if string_length is not None and string
        else string
    )


class CorrelationIdLogFilter:
    """Logging filter to attached correlation IDs to log records"""

    def __init__(
        self, uuid_length: int | None = None, fallback: str | None = None
    ):
        self.uuid_length = uuid_length
        self.fallback = fallback

    def filter(self, record: "LogRecord") -> bool:
        if value := correlation_id_var.get(self.fallback):
            value = str(value)
            record.correlation_id = _trim_string(value, self.uuid_length)
        return True
