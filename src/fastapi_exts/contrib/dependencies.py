from typing import Annotated

from fastapi import Request
from fastapi.datastructures import State
from fastapi.params import Depends
from starlette.types import Scope


def request_user_agent(request: Request):
    return request.headers.get("user-agent")


RequestUserAgent = Annotated[str | None, Depends(request_user_agent)]


def request_scope(request: Request):
    return request.scope


RequestScope = Annotated[Scope, Depends(request_scope)]


def request_state(request: Request):
    return request.state


RequestState = Annotated[State, Depends(request_state)]
