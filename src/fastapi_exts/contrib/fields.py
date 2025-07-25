from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, Field

from fastapi_exts._utils import naive_datetime, utc_datetime


DBSmallInt = Annotated[int, Field(ge=-32768, le=32767)]
DBInt = Annotated[int, Field(ge=-2147483648, le=2147483647)]
DBBigInt = Annotated[
    int, Field(ge=-9223372036854775808, le=9223372036854775807)
]
DBSmallSerial = Annotated[int, Field(ge=1, le=32767)]
DBIntSerial = Annotated[int, Field(ge=1, le=2147483647)]
DBBigintSerial = Annotated[int, Field(ge=1, le=9223372036854775807)]


NaiveDatetime = Annotated[datetime, AfterValidator(naive_datetime)]
"""去除时区信息"""

UTCDateTime = Annotated[datetime, AfterValidator(utc_datetime)]
"""将时区转成 UTC"""

UTCNaiveDateTime = Annotated[
    datetime,
    AfterValidator(lambda x: naive_datetime(utc_datetime(x))),
]
"""将时间转成 UTC, 并且去除时区信息"""
