from typing import TYPE_CHECKING

from .constants import LOG_EXTRA_KEY
from .context import request_info_var


if TYPE_CHECKING:
    from logging import LogRecord


class RequestInfoLogFilter:
    def filter(self, record: "LogRecord") -> bool:
        setattr(record, LOG_EXTRA_KEY, request_info_var.get(None))
        return True
