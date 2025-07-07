from fastapi_exts.exceptions import HTTPProblem


class WTF(HTTPProblem):
    type = "urn:problem-type:wtf"
    title = "WTF"


def test_http_problem():
    data = WTF().data
    assert data.type == "urn:problem-type:wtf"
    assert data.title == "WTF"
