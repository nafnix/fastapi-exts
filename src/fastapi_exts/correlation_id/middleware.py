import inspect
import logging
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .constants import HEADER_NAME, STATE_KEY
from .context import correlation_id_var
from .types import CorrelationIDGenerator, CorrelationIDValidator


logger = logging.getLogger("fastapi-exts.correlation_id")


class CorrelationIDMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        id_generator: CorrelationIDGenerator = lambda: str(uuid.uuid4()),
        id_validator: CorrelationIDValidator | None = None,
    ) -> None:
        self.app = app
        self.generator = id_generator
        self.validator = id_validator

    async def _gen(self):
        result = self.generator()
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _verify_header_value(self, header_value: str):
        if self.validator:
            valid_value = self.validator(header_value)
            if inspect.isawaitable(valid_value):
                await valid_value

            if valid_value:
                return header_value

            result = await self._gen()

            logger.warning(
                "New correlation ID generated due to validation failure",
                extra={"failure": header_value, "new_value": result},
            )
            return result
        return header_value

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
            value = await self._gen()
            logger.debug(
                "Correlation ID generated",
                extra={"correlation_id": str(value)},
            )
        else:
            value = await self._verify_header_value(header_value)

        scope.setdefault("state", {}).update({STATE_KEY: value})
        headers.setdefault(HEADER_NAME, str(value))

        correlation_id_var.set(value)

        async def send_(message: Message):
            if message["type"] == "http.response.start" and (
                value := scope.get("state", {}).get(STATE_KEY)
            ):
                headers = MutableHeaders(scope=message)
                headers.setdefault(HEADER_NAME, str(value))

            await send(message)

        await self.app(scope, receive, send_)
