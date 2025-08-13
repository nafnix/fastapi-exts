from collections.abc import Awaitable, Callable
from inspect import isawaitable
from typing import Any, cast

from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse, JSONResponse
from scalar_fastapi import get_scalar_api_reference
from starlette.routing import Route

from fastapi_exts.core import ExtensionBase
from fastapi_exts.utils.paths import URLPath


OpenAPIModifier = Callable[
    [dict[str, Any]], dict[str, Any] | Awaitable[dict[str, Any]]
]


class OpenAPIExtension(ExtensionBase):
    name = "openapi"

    def _add_openapi(
        self,
        path: str,
        root_path: str | None = None,
    ):
        @self.app.get(path, include_in_schema=False)
        async def get_openapi() -> JSONResponse:
            if (
                root_path not in self.server_urls
                and root_path
                and self.app.root_path_in_servers
            ):
                self.app.servers.insert(0, {"url": root_path})
                self.server_urls.add(root_path)

            openapi = self.app.openapi()

            for i in self._modifiers:
                _openapi = i(openapi)
                openapi = (
                    (await _openapi) if isawaitable(_openapi) else _openapi
                )

            return JSONResponse(openapi)

    def _add_swagger(
        self,
        openapi_url: str,
        path: str,
        oauth2_redirect_url: str | None,
    ):
        @self.app.get(path, include_in_schema=False)
        async def swagger_ui() -> HTMLResponse:
            return get_swagger_ui_html(
                openapi_url=openapi_url,
                title=f"{self.app.title} - Swagger UI",
                oauth2_redirect_url=oauth2_redirect_url,
                init_oauth=self.app.swagger_ui_init_oauth,
                swagger_ui_parameters=self.app.swagger_ui_parameters,
            )

        if oauth2_redirect_url:

            @self.app.get(oauth2_redirect_url, include_in_schema=False)
            async def swagger_ui_redirect() -> HTMLResponse:
                return get_swagger_ui_oauth2_redirect_html()

    def _add_redoc(
        self,
        openapi_url: str,
        path: str,
    ):
        @self.app.get(path, include_in_schema=False)
        async def redoc_html() -> HTMLResponse:
            return get_redoc_html(
                openapi_url=openapi_url,
                title=f"{self.app.title} - ReDoc",
            )

    def _add_scalar(
        self,
        openapi_url: str,
        path: str,
    ):
        @self.app.get(path, include_in_schema=False)
        async def scalar_html() -> HTMLResponse:
            return get_scalar_api_reference(
                openapi_url=openapi_url,
                title=f"{self.app.title} - Scalar",
                servers=[],
            )

    def __init__(
        self,
        *,
        enabled: bool = True,
        root_path: str | None = None,
        openapi_url: str | None = "/openapi.json",
        docs_openapi_url: str | None = None,
        swagger_url: str | None = "/openapi/swagger",
        swagger_oauth2_redirect_url: str
        | None = "/openapi/swagger/oauth2-redirect",
        scalar_url: str | None = "/openapi/scalar",
        redoc_url: str | None = "/openapi/redoc",
    ) -> None:
        self._modifiers: set[OpenAPIModifier] = set()
        self._root_path = root_path
        self._openapi_url = openapi_url
        if docs_openapi_url is None and openapi_url is not None:
            docs_openapi_url = URLPath(openapi_url)
            if root_path is not None:
                docs_openapi_url = URLPath(root_path) / docs_openapi_url

        self._docs_openapi_url = docs_openapi_url

        self._enabled = enabled

        self._swagger_url = swagger_url
        self._swagger_oauth2_redirect_url = swagger_oauth2_redirect_url
        self._redoc_url = redoc_url
        self._scalar_url = scalar_url

    def _remove_default(self, app: FastAPI):
        exclude = [
            i
            for i in app.routes
            if hasattr(i, "path")
            and (
                cast(Route, i).path
                in [
                    app.docs_url,
                    app.redoc_url,
                    app.openapi_url,
                    app.swagger_ui_oauth2_redirect_url,
                ]
            )
        ]
        for i in exclude:
            app.routes.remove(i)

    def add_modifier(self, modifier: OpenAPIModifier):
        self._modifiers.add(modifier)

    def setup(self, app: FastAPI):
        self._remove_default(app)

        urls = (server_data.get("url") for server_data in app.servers)
        self.server_urls = {url for url in urls if url}
        self.app = app

        if self._enabled:
            if self._openapi_url is not None:
                self._add_openapi(self._openapi_url, self._root_path)

            if self._docs_openapi_url is not None:
                if self._swagger_url:
                    self._add_swagger(
                        self._docs_openapi_url,
                        self._swagger_url,
                        self._swagger_oauth2_redirect_url,
                    )

                if self._redoc_url:
                    self._add_redoc(self._docs_openapi_url, self._redoc_url)

                if self._scalar_url:
                    self._add_scalar(self._docs_openapi_url, self._scalar_url)
