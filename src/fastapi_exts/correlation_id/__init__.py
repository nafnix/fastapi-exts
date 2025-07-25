from fastapi import Depends, FastAPI

from fastapi_exts._utils import merge

from .constants import HEADER_NAME
from .context import correlation_id_var
from .dependencies import CorrelationID, get_correlation_id
from .log import CorrelationIdLogFilter
from .middleware import CorrelationIDMiddleware


class CorrelationIDExtension:
    def setup(self, app: FastAPI):
        app.add_middleware(CorrelationIDMiddleware)

        app.router.dependencies.append(Depends(get_correlation_id))
        extra = {
            "headers": {
                HEADER_NAME: {
                    "schema": {
                        "type": "string",
                        "format": "uuid",
                        "title": HEADER_NAME,
                    },
                },
            }
        }
        merge(app.router.responses, extra)


__all__ = [
    "CorrelationID",
    "CorrelationIDExtension",
    "CorrelationIdLogFilter",
    "correlation_id_var",
    "get_correlation_id",
]
