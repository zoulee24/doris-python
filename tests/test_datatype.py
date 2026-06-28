"""``datatype.parse_sqltype`` 单元测试。

覆盖:
* 所有 _type_map 中登记的 Doris 类型
* 带/不带参数的版本(varchar(64)、decimal(18,2) 等)
* 边界情况:未知类型、空格、大小写、空 options
"""

from __future__ import annotations

import datetime
from typing import Any

import pytest
from sqlalchemy.sql import sqltypes

from doris_python.sqlalchemy import datatype


# ---- 1. 基础类型映射(无参数) ---------------------------------------------

@pytest.mark.parametrize(
    ("type_str", "expected_cls"),
    [
        # 布尔
        ("boolean", sqltypes.BOOLEAN),
        # 整型
        ("tinyint", datatype.TINYINT),
        ("smallint", sqltypes.SMALLINT),
        ("int", sqltypes.INTEGER),
        ("integer", sqltypes.INTEGER),
        ("bigint", sqltypes.BIGINT),
        ("largeint", datatype.LARGEINT),
        # 浮点
        ("float", sqltypes.FLOAT),
        ("double", datatype.DOUBLE),
        # 字符串
        ("text", sqltypes.TEXT),
        ("string", sqltypes.String),
        ("json", sqltypes.JSON),
        ("jsonb", sqltypes.JSON),
        # 时间
        ("date", sqltypes.DATE),
        ("datetime", sqltypes.DATETIME),
        ("time", datatype.TIME),
        # 结构化
        ("array", datatype.ARRAY),
        ("map", datatype.MAP),
        ("struct", datatype.STRUCT),
        ("hll", datatype.HLL),
        ("bitmap", datatype.BITMAP),
        ("quantile_state", datatype.QUANTILE_STATE),
        ("agg_state", datatype.AGG_STATE),
        # 网络
        ("ipv4", datatype.IPV4),
        ("ipv6", datatype.IPV6),
        # 半结构化
        ("variant", datatype.VARIANT),
    ],
)
def test_parse_sqltype_basic(type_str: str, expected_cls: type) -> None:
    """无参数时,基础类型应映射到对应的 SQLAlchemy 类型类。"""
    result = datatype.parse_sqltype(type_str)
    assert isinstance(result, expected_cls)


# ---- 2. 带长度参数的字符串类型 -------------------------------------------

@pytest.mark.parametrize(
    ("type_str", "expected_length"),
    [
        ("varchar(64)", 64),
        ("varchar(255)", 255),
        ("char(10)", 10),
        ("char(1)", 1),
        ("string(32)", 32),
    ],
)
def test_parse_sqltype_with_length(type_str: str, expected_length: int) -> None:
    """varchar/char/string 应正确解析 length。"""
    result = datatype.parse_sqltype(type_str)
    assert result.length == expected_length


# ---- 3. 带 precision/scale 的 decimal -----------------------------------

@pytest.mark.parametrize(
    ("type_str", "expected_precision", "expected_scale"),
    [
        ("decimal(18,2)", 18, 2),
        ("decimal(10,0)", 10, 0),
        ("decimalv2(20,4)", 20, 4),
        ("decimalv3(38, 6)", 38, 6),  # 容许空格
    ],
)
def test_parse_sqltype_decimal(
    type_str: str, expected_precision: int, expected_scale: int
) -> None:
    """decimal/decimalv2/decimalv3 应解析 precision 与 scale。"""
    result = datatype.parse_sqltype(type_str)
    assert isinstance(result, sqltypes.DECIMAL)
    assert result.precision == expected_precision
    assert result.scale == expected_scale


def test_parse_sqltype_decimal_default_scale() -> None:
    """只指定 precision 时,scale 默认 0。"""
    result = datatype.parse_sqltype("decimal(18)")
    assert result.precision == 18
    assert result.scale == 0


# ---- 4. 大小写与空白 -----------------------------------------------------

@pytest.mark.parametrize(
    "type_str",
    [
        "VARCHAR(32)",
        "  varchar(32)  ",
        "BigInt",
        "DECIMAL(10,2)",
    ],
)
def test_parse_sqltype_case_and_whitespace(type_str: str) -> None:
    """应忽略大小写与首尾空白。"""
    result = datatype.parse_sqltype(type_str)
    assert not isinstance(result, sqltypes.NullType)


# ---- 5. 容错处理 ---------------------------------------------------------

def test_parse_sqltype_unknown_type_returns_nulltype() -> None:
    """未知类型返回 NULLTYPE,不应抛异常。"""
    result = datatype.parse_sqltype("nonexistent_type")
    assert isinstance(result, sqltypes.NullType)


def test_parse_sqltype_garbage_returns_nulltype() -> None:
    """完全无法解析的字符串也返回 NULLTYPE。"""
    # 没有合法 ``type(...)`` 前缀,正则不匹配
    result = datatype.parse_sqltype("!!!")
    assert isinstance(result, sqltypes.NullType)


def test_parse_sqltype_empty_string_returns_nulltype() -> None:
    """空字符串返回 NULLTYPE。"""
    result = datatype.parse_sqltype("")
    assert isinstance(result, sqltypes.NullType)


# ---- 6. python_type 契约 -------------------------------------------------

@pytest.mark.parametrize(
    ("type_str", "expected_py"),
    [
        ("array", list),
        ("map", dict),
        ("ipv4", str),
        ("ipv6", str),
        ("time", datetime.timedelta),
        ("variant", dict),
    ],
)
def test_parse_sqltype_python_type(type_str: str, expected_py: Any) -> None:
    """涉及嵌套/特殊类型的 ``python_type`` 属性应符合预期。"""
    result = datatype.parse_sqltype(type_str)
    assert result.python_type is expected_py