from typing import NotRequired, TypedDict

from pydantic import HttpUrl


class ServerConfig(TypedDict):
    url: NotRequired[HttpUrl | str]
    description: NotRequired[str]


def servers(*configs: ServerConfig):
    results: list[dict[str, str]] = []
    for config in configs:
        i = {}
        if url := config.get("url"):
            if isinstance(url, str):
                i["url"] = url
            else:
                i["url"] = url.unicode_string()

        if desc := config.get("description"):
            i["description"] = desc

        if i:
            results.append(i)

    return results
