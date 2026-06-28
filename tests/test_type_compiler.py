"""``DorisTypeCompiler`` 单元测试。

覆盖所有 ``visit_*`` 方法以及 ``_extend_numeric`` 的 UNSIGNED/ZEROFILL
抑制逻辑。无需数据库。
"""

from __future__ import annotations

import pytest
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.dialects.mysql import DOUBLE as MySQL_DOUBLE
from sqlalchemy.dialects.mysql import TINYINT as MySQL_TINYINT

from doris_python.sqlalchemy import datatype
from doris_python.sqlalchemy.dialect import DorisDDLCompiler, DorisTypeCompiler


@pytest.fixture
def doris_dialect():
    return create_engine("doris+pymysql://u:p@h:9030/db").dialect


@pytest.fixture
def type_compiler(doris_dialect):
    return DorisTypeCompiler(doris_dialect)


def _compile(column: Column) -> str:
    """用 DorisDDLCompiler 直接编译单个列的类型片段。"""
    md = type(column).metadata  # not used, kept for symmetry
    table = Table("t", md, column)
    # ``get_column_specification`` 返回的就是 ``colname TYPE ...`` 的整串
    ddl_compiler = DorisDDLCompiler(table.bind.dialect, None) if table.bind else None
    return ""


def _type_str(column: Column, doris_dialect) -> str:
    """用 DorisTypeCompiler 取出 ``TYPE`` 部分(不含列名)。"""
    compiler = DorisTypeCompiler(doris_dialect)
    return compiler.process(column.type)


# ---- 1. 基本 visit_* 一对一映射 ------------------------------------------

@pytest.mark.parametrize(
    ("type_obj", "expected_ddl"),
    [
        (datatype.TINYINT(), "TINYINT"),
        (datatype.LARGEINT(), "LARGEINT"),
        (datatype.DOUBLE(), "DOUBLE"),
        (datatype.HLL(), "HLL"),
        (datatype.BITMAP(), "BITMAP"),
        (datatype.QUANTILE_STATE(), "QUANTILE_STATE"),
        (datatype.AGG_STATE(), "AGG_STATE"),
        (datatype.ARRAY(), "ARRAY"),
        (datatype.MAP(), "MAP"),
        (datatype.STRUCT(), "STRUCT"),
        (datatype.IPV4(), "IPV4"),
        (datatype.IPV6(), "IPV6"),
        (datatype.TIME(), "TIME"),
        (datatype.VARIANT(), "VARIANT"),
    ],
)
def test_visit_returns_doris_type_name(type_obj, expected_ddl: str, doris_dialect) -> None:
    """每个 Doris 专属类型应生成对应的大写类型名。"""
    compiler = DorisTypeCompiler(doris_dialect)
    assert compiler.process(type_obj) == expected_ddl


# ---- 2. UNSIGNED / ZEROFILL 抑制 ----------------------------------------

def test_unsigned_stripped_from_integer(doris_dialect) -> None:
    """MySQL 的 UNSIGNED 修饰符在 Doris 中不存在,应被剥离。"""
    # ``mysql.INTEGER(unsigned=True)`` 会生成 ``int(11) unsigned``
    from sqlalchemy.dialects.mysql import INTEGER as MySQL_INTEGER

    compiler = DorisTypeCompiler(doris_dialect)
    ddl = compiler.process(MySQL_INTEGER(unsigned=True))
    assert "UNSIGNED" not in ddl.upper()


def test_zerofill_stripped(doris_dialect) -> None:
    """ZEROFILL 同样应被剥离。"""
    from sqlalchemy.dialects.mysql import INTEGER as MySQL_INTEGER

    compiler = DorisTypeCompiler(doris_dialect)
    ddl = compiler.process(MySQL_INTEGER(zerofill=True))
    assert "ZEROFILL" not in ddl.upper()


# ---- 3. 通用类型仍走 MySQL 父类逻辑(回归保护) --------------------------

@pytest.mark.parametrize(
    ("type_obj", "expected_fragment"),
    [
        (Integer(), "INT"),
        (BigInteger(), "BIGINT"),
        (SmallInteger(), "SMALLINT"),
        (Float(), "FLOAT"),
        # MySQLDialect 的父类把 Numeric 渲染为 NUMERIC 而非 DECIMAL
        (Numeric(10, 2), "NUMERIC"),
        (String(64), "VARCHAR"),
        (Text(), "TEXT"),
        (DateTime(), "DATETIME"),
    ],
)
def test_generic_types_render(type_obj, expected_fragment: str, doris_dialect) -> None:
    """标准 SQLAlchemy 类型应能正常被 DorisTypeCompiler 处理。"""
    compiler = DorisTypeCompiler(doris_dialect)
    ddl = compiler.process(type_obj)
    assert expected_fragment in ddl.upper()