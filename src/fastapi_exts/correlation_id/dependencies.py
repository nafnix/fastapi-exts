from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header

from fastapi_exts.contrib.dependencies import RequestScope

from .constants import HEADER_NAME, SCOPE_KEY


def get_correlation_id(
    scope: RequestScope,
    _scheme: UUID = Header(None, alias=HEADER_NAME),
) -> UUID:
    return scope[SCOPE_KEY]


CorrelationID = Annotated[
    UUID,
    Depends(get_correlation_id),
]
