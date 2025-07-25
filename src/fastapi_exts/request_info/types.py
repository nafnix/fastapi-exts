from collections.abc import Callable
from typing import Any, NotRequired, TypedDict

from starlette.requests import Request


class RequestUserInfo(TypedDict):
    user_id: NotRequired[Any]
    username: NotRequired[str]


class RequestInfo(RequestUserInfo):
    http_version: str
    """HTTP 版本"""

    method: str
    """请求方式"""
    url: str
    """请求 URL"""
    path: str
    """请求路径"""
    client_ip: str | None
    """请求来源的 IP"""

    user_agent: NotRequired[str | None]
    """请求 UA"""

    status_code: NotRequired[int]
    """响应状态码"""

    duration: NotRequired[float]
    """执行耗时（毫秒）"""


GetClientIP = Callable[[Request], str | None]
