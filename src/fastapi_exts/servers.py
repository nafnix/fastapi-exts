from typing import NotRequired, TypedDict

from pydantic import HttpUrl


class ServerConfig(TypedDict):
    url: HttpUrl | str
    description: NotRequired[str]


def servers(*configs: ServerConfig | HttpUrl | str):
    results: list[dict[str, str]] = []
    for config in configs:
        i = {}
        if isinstance(config, str):
            i["url"] = config
        elif isinstance(config, HttpUrl):
            i["url"] = config.encoded_string()
        else:
            if url := config["url"]:
                if isinstance(url, str):
                    i["url"] = url
                else:
                    i["url"] = url.unicode_string()

            if desc := config.get("description"):
                i["description"] = desc

        results.append(i)

    return results
