from collections.abc import Awaitable, Callable


CorrelationIDGenerator = Callable[[], str | Awaitable[str]]
CorrelationIDValidator = Callable[[str], bool | Awaitable[bool]]
