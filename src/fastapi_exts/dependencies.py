from typing import Annotated

from fastapi import Request
from fastapi.params import Depends
from starlette.types import Scope


def request_user_agent(request: Request):
    return request.headers.get("user-agent")


RequestUserAgent = Annotated[str | None, Depends(request_user_agent)]


def request_scope(request: Request):
    return request.scope


RequestScope = Annotated[Scope, Depends(request_scope)]
