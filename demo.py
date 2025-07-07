from fastapi import FastAPI

from fastapi_exts.exceptions import (
    BaseHTTPError,
    HTTPProblem,
    ext_http_error_handler,
)
from fastapi_exts.responses import build_responses


app = FastAPI()
app.exception_handlers[BaseHTTPError] = ext_http_error_handler

HTTPProblem.title = "lala"
HTTPProblem.type = "urn:problem:lala"


@app.get("/", responses=build_responses(HTTPProblem))
async def demo():
    raise HTTPProblem
