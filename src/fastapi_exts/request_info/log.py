from typing import TYPE_CHECKING

from .context import request_info_var


if TYPE_CHECKING:
    from logging import LogRecord


class RequestInfoLogFilter:
    def filter(self, record: "LogRecord") -> bool:
        record.request_info = request_info_var.get(None)
        return True
