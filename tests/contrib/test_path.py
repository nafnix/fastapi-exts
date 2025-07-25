from fastapi_exts.contrib.path import Path


class TestPath:
    def test_path(self):
        value = Path("123") / "123" / 123
        assert value == "/123/123/123"

    def test_another_separator_path(self):
        class DotPath(Path):
            __separator__ = "."
            __startswith_separator__ = False

        value = DotPath("123") / "123" / 123
        assert value == "123.123.123"

    def test_with_prefix(self):
        class PrefixPath(Path):
            __prefix__ = "abc"

        value = PrefixPath("123") / "123" / 123
        assert value == "/abc/123/123/123"

    def test_another_separator_with_prefix(self):
        class _Path(Path):
            __separator__ = "."
            __startswith_separator__ = False
            __prefix__ = "abc"

        value = _Path("123") / "123" / 123
        assert value == "abc.123.123.123"
