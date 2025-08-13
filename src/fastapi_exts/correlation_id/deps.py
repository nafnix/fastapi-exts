from typing import Annotated

from fastapi import Depends, Header

from .constants import HEADER_NAME


def get_correlation_id(value: str = Header(None, alias=HEADER_NAME)) -> str:
    return value


CorrelationID = Annotated[
    str,
    Depends(get_correlation_id),
]
