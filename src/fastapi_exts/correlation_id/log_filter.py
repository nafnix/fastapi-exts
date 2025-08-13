from .constants import FALLBACK_VALUE, LOG_EXTRA_NAME
from .context import correlation_id_var


def _trim_string(string: str | None, string_length: int | None) -> str | None:
    return (
        string[:string_length]
        if string_length is not None and string
        else string
    )


class CorrelationIdLogFilter:
    """Logging filter to attached correlation IDs to log records"""

    def __init__(
        self,
        value_length: int | None = None,
    ):
        self.value_length = value_length

    def filter(self, record) -> bool:
        value = correlation_id_var.get(FALLBACK_VALUE)
        value = _trim_string(value, self.value_length)
        setattr(record, LOG_EXTRA_NAME, value)
        return True
