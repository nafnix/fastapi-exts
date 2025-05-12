from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request


IP_HEADERS = [
    "X-Forwarded-For",  # 最常见的, 用于传递客户端 IP
    "X-Real-IP",  # 一些代理服务器使用, 如 Nginx
    "Proxy-Client-IP",  # 一些代理服务器或应用使用
    "WL-Proxy-Client-IP",  # WebLogic 服务器代理使用
    "HTTP_CLIENT_IP",  # 某些环境下的自定义头
    "HTTP_X_FORWARDED_FOR",  # 某些环境下的自定义头
    "CF-Connecting-IP",  # Cloudflare 使用
    "True-Client-IP",  # Akamai 使用
    "X-Cluster-Client-IP",  # 某些负载均衡器使用
    "Fastly-Client-IP",  # Fastly CDN 使用
    "Forwarded",  # 标准化头, RFC 7239 定义
]


def request_ip(request: Request):
    headers = request.headers

    for i in IP_HEADERS:
        result = headers.get(i)
        if result:
            return result

    if request.client:
        return request.client.host

    return "127.0.0.1"


RequestIP = Annotated[str | None, Depends(request_ip)]


def request_user_agent(request: Request):
    return request.headers.get("user-agent")


RequestUserAgent = Annotated[str | None, Depends(request_user_agent)]


@dataclass
class Info:
    id: str
    time: datetime
    ip: str | None = None
    ua: str | None = None


def request_info(
    request: Request,
    request_ip: RequestIP,
    request_user_agent: RequestUserAgent,
):
    return Info(
        id=request.headers["x-request-id"],
        time=datetime.now(UTC),
        ip=request_ip,
        ua=request_user_agent,
    )


RequestInfo = Annotated[Info, Depends(request_info)]
