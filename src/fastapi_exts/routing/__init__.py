from collections.abc import Callable
from typing import Any

from fastapi import routing

from fastapi_exts.responses import build_responses
from fastapi_exts.routing.utils import analyze_and_update


class ExtAPIRoute(routing.APIRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        responses: dict[int | str, dict[str, Any]] | None = None,
        **kwds,
    ):
        responses = responses or {}
        for i in analyze_and_update(endpoint):
            responses.update(build_responses(*i.exceptions))
            if i.provider:
                responses.update(build_responses(*i.provider.exceptions))

        super().__init__(path, endpoint, responses=responses, **kwds)


class ExtWebSocketRoute(routing.APIWebSocketRoute):
    def __init__(
        self, path: str, endpoint: Callable[..., Any], **kwds
    ) -> None:
        analyze_and_update(endpoint)
        super().__init__(path, endpoint, **kwds)


class ExtAPIRouter(routing.APIRouter):
    def add_api_route(
        self,
        path: str,
        endpoint: Callable,
        responses: dict[int | str, dict[str, Any]] | None = None,
        **kwds,
    ):
        responses = responses or {}
        for i in analyze_and_update(endpoint):
            responses.update(build_responses(*i.exceptions))
            if i.provider:
                responses.update(build_responses(*i.provider.exceptions))

        super().add_api_route(path, endpoint, responses=responses, **kwds)

    def add_api_websocket_route(
        self, path: str, endpoint: Callable[..., Any], *args, **kwds
    ):
        analyze_and_update(endpoint)
        super().add_api_websocket_route(path, endpoint, *args, **kwds)
