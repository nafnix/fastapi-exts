import uuid
from contextvars import ContextVar


correlation_id_var: ContextVar[uuid.UUID | None] = ContextVar(
    "correlation_id", default=None
)
