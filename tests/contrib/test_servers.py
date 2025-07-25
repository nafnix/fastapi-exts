from fastapi_exts.contrib.servers import servers


def test_servers():
    result = servers("/asdasd", {"url": ""}, {"url": "/123"})
    assert result == [{"url": "/asdasd"}, {"url": "/123"}]
