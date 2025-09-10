from typing import Annotated

from pydantic import Field


DBSmallInt = Annotated[int, Field(ge=-32768, le=32767)]
DBInt = Annotated[int, Field(ge=-2147483648, le=2147483647)]
DBBigInt = Annotated[
    int, Field(ge=-9223372036854775808, le=9223372036854775807)
]
DBSmallSerial = Annotated[int, Field(ge=1, le=32767)]
DBIntSerial = Annotated[int, Field(ge=1, le=2147483647)]
DBBigintSerial = Annotated[int, Field(ge=1, le=9223372036854775807)]
