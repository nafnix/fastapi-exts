import time

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .constants import SCOPE_NAME
from .context import request_info_var
from .types import GetClientIP, RequestInfo


class RequestInfoMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        get_client_ip: GetClientIP,
    ):
        self.app = app
        self.get_client_ip = get_client_ip

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        info = RequestInfo(
            http_version=scope["http_version"],
            method=scope["method"],
            url=str(request.url),
            path=scope["path"],
            client_ip=self.get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        start_time = time.perf_counter()
        request_info_var.set(info)

        async def send_wrapper(message: Message):
            info.update(scope.get(SCOPE_NAME, {}))
            match message["type"]:
                case "http.response.start":
                    info["status_code"] = message["status"]
                    info["duration"] = (time.perf_counter() - start_time) * 1e3

            request_info_var.set(info)

            await send(message)

        await self.app(scope, receive, send_wrapper)
