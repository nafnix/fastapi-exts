import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .constants import HEADER_NAME, SCOPE_KEY
from .context import correlation_id_var as ctx


class CorrelationIDMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    @staticmethod
    async def _check_header_value(header_value: str):
        try:
            value = uuid.UUID(header_value)
        except ValueError:
            value = uuid.uuid4()

        return value

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        headers = MutableHeaders(scope=scope)
        header_value = headers.get(HEADER_NAME.lower())

        if header_value is None:
            value = uuid.uuid4()
        else:
            value = await self._check_header_value(header_value)

        scope.update({SCOPE_KEY: value})
        headers.update({HEADER_NAME: str(value)})

        ctx.set(value)

        async def send_(message: Message):
            if message["type"] == "http.response.start" and (
                value := scope.get(SCOPE_KEY)
            ):
                headers = MutableHeaders(scope=message)
                headers.setdefault(HEADER_NAME, str(value))

            await send(message)

        await self.app(scope, receive, send_)
