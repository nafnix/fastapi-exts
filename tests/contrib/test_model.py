from datetime import UTC, datetime

from pydantic import create_model

from fastapi_exts.contrib import models as m


class TestAPIModel:
    def test_camel(self):
        class Demo(m.APIModel):
            a_b: str

        value = "123"
        result = Demo(a_b=value).model_dump()
        assert result["aB"] == value

        model = create_model("Demo2", b_c=str, __base__=(m.APIModel))
        result = model.model_validate({"b_c": value}).model_dump()
        assert result["bC"] == value

        result = model.model_validate({"bC": value}).model_dump()
        assert result["bC"] == value


class TestUTCDatetimeModel:
    def test_to_utc(self):
        class Demo(m.UTCDatetimeModel):
            dt: datetime
            dt2: datetime = datetime.now()

        result = Demo(dt=datetime.now())
        assert result.dt.tzinfo is UTC
        assert result.dt2.tzinfo is UTC


class TestNaiveDatetimeModel:
    def test_to_naive(self):
        class Demo(m.NaiveDatetimeModel):
            dt: datetime
            dt2: datetime = datetime.now(tz=UTC)

        result = Demo(dt=datetime.now(tz=UTC))
        assert result.dt.tzinfo is None
        assert result.dt2.tzinfo is None


class TestNaiveUTCDatetimeModel:
    def test_to_naive(self):
        class Demo(m.NaiveUTCModel):
            dt: datetime
            dt2: datetime = datetime.now()

        result = Demo(dt=datetime.now())
        assert result.dt.tzinfo is None
        assert result.dt2.tzinfo is None
