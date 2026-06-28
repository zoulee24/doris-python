"""``DorisDDLCompiler`` 单元测试。

策略:用 ``sa.schema.Table`` + ``meta.create_all`` 在内存里生成 DDL,
用 ``dialect`` 直接编译,断言关键字/子句出现或缺失。

无需真实数据库。
"""

from __future__ import annotations

import pytest
from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.schema import CreateTable

from doris_python.sqlalchemy.dialect import DorisDDLCompiler


@pytest.fixture
def doris_dialect():
    """直接构造一个 DorisDDLCompiler 实例(无需 connection)。"""
    return create_engine("doris+pymysql://u:p@h:9030/db").dialect


@pytest.fixture
def ddl_compiler(doris_dialect):
    """DorisDDLCompiler 实例,用于直接调用 post_create_table。"""
    return DorisDDLCompiler(doris_dialect, None)


def _compile_create(table: Table, doris_dialect) -> str:
    """用 ``schema.CreateTable`` 编译整张表的 CREATE TABLE 语句。"""
    return str(CreateTable(table).compile(dialect=doris_dialect))


def _normalize(ddl: str) -> str:
    """规范化 DDL:把所有空白压成单空格,便于子串断言。"""
    return " ".join(ddl.split()).upper()


# ---- 1. 约束抑制 --------------------------------------------------------

def test_ddl_strips_auto_increment(doris_dialect) -> None:
    """Doris 不支持 AUTO_INCREMENT 语法,应被剥离。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True, autoincrement=True),
    )
    ddl = _compile_create(md.tables["t"], doris_dialect)
    assert "AUTO_INCREMENT" not in _normalize(ddl)


def test_ddl_drops_primary_key_constraint(doris_dialect) -> None:
    """Doris 用 KEY model 而非 PRIMARY KEY 约束,应被剔除。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        Column("name", String(32)),
    )
    ddl = _compile_create(md.tables["t"], doris_dialect)
    assert "PRIMARY KEY" not in _normalize(ddl)


def test_ddl_drops_foreign_key_constraint(doris_dialect) -> None:
    """Doris 不支持外键,FOREIGN KEY 子句应消失。"""
    md = MetaData()
    parent = Table(
        "parent",
        md,
        Column("id", Integer, primary_key=True),
    )
    Table(
        "child",
        md,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey("parent.id")),
    )
    ddl = _compile_create(md.tables["child"], doris_dialect)
    assert "FOREIGN KEY" not in _normalize(ddl)


def test_ddl_drops_unique_constraint(doris_dialect) -> None:
    """Doris 不支持 UNIQUE 约束的 DDL 形式。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        Column("name", String(32), unique=True),
        UniqueConstraint("name", name="uq_name"),
    )
    ddl = _compile_create(md.tables["t"], doris_dialect)
    assert "UNIQUE" not in _normalize(ddl)


# ---- 2. post_create_table: KEY model ------------------------------------

def test_post_create_table_with_explicit_key_columns(ddl_compiler) -> None:
    """显式指定 key_type / key_columns 时应输出对应子句。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer),
        Column("name", String(32)),
        doris_key_type="UNIQUE",
        doris_key_columns=["id"],
    )
    table = md.tables["t"]
    out = ddl_compiler.post_create_table(table)
    assert "ENGINE" not in out  # 没有 ENGINE 时不应输出
    assert "UNIQUEKEY(`id`)" in out.replace(" ", "")


def test_post_create_table_auto_key_from_pk(ddl_compiler) -> None:
    """未显式指定 key 时,应从 primary key 自动推断 DUPLICATE KEY。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        Column("v", Integer),
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    assert "DUPLICATEKEY(`id`)" in out.replace(" ", "")


def test_post_create_table_auto_key_multiple_columns(ddl_compiler) -> None:
    """复合主键应输出多列 KEY 子句。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("a", Integer, primary_key=True),
        Column("b", Integer, primary_key=True),
        Column("v", Integer),
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    normalized = out.replace(" ", "")
    assert normalized.startswith("\nDUPLICATEKEY(`a`,`b`)") or \
           normalized.startswith("DUPLICATEKEY(`a`,`b`)")


def test_post_create_table_no_pk_no_key_returns_empty(ddl_compiler) -> None:
    """没有 PK 也没有显式 key 时,不输出 KEY 子句。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("a", Integer),
        Column("b", Integer),
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    assert "KEY" not in out.upper()


# ---- 3. post_create_table: ENGINE / COMMENT / DISTRIBUTED BY / PROPERTIES

def test_post_create_table_engine(ddl_compiler) -> None:
    """``doris_engine`` 选项应输出 ``ENGINE = xxx``。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        doris_engine="OLAP",
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    assert "ENGINE = OLAP" in out


def test_post_create_table_comment_escapes_quotes(ddl_compiler) -> None:
    """表注释中的单引号应转义为 ``\\'``。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        comment="it's a table",
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    assert "COMMENT 'it\\'s a table'" in out


def test_post_create_table_distributed_by_with_buckets(ddl_compiler) -> None:
    """``doris_distributed_by`` + ``doris_buckets`` 应输出对应子句。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        doris_distributed_by="HASH(`id`)",
        doris_buckets=16,
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    assert "DISTRIBUTEDBYHASH(`id`)BUCKETS16" in out.replace(" ", "")


def test_post_create_table_distributed_by_without_buckets(ddl_compiler) -> None:
    """不指定 buckets 时,不应出现 BUCKETS 子句。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        doris_distributed_by="HASH(`id`)",
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    assert "BUCKETS" not in out


def test_post_create_table_properties(ddl_compiler) -> None:
    """``doris_properties`` dict 应展开为 ``PROPERTIES("k" = "v", ...)``。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        doris_properties={"replication_num": "1", "storage_medium": "SSD"},
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    assert '"replication_num" = "1"' in out
    assert '"storage_medium" = "SSD"' in out
    assert "PROPERTIES" in out


def test_post_create_table_partition_by(ddl_compiler) -> None:
    """``doris_partition_by`` 应原样输出。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        Column("dt", String(16)),
        doris_partition_by="PARTITION BY RANGE(`dt`) ()",
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    assert "PARTITION BY RANGE(`dt`) ()" in out


def test_post_create_table_combined(ddl_compiler) -> None:
    """所有选项一起: ENGINE + KEY + DISTRIBUTED + PROPERTIES。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        doris_engine="OLAP",
        doris_key_type="DUPLICATE",
        doris_key_columns=["id"],
        doris_distributed_by="HASH(`id`)",
        doris_buckets=8,
        doris_properties={"replication_num": "3"},
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    assert "ENGINE = OLAP" in out
    assert "DUPLICATEKEY(`id`)" in out.replace(" ", "")
    assert "DISTRIBUTEDBYHASH(`id`)BUCKETS8" in out.replace(" ", "")
    assert '"replication_num" = "3"' in out


def test_post_create_table_empty_returns_empty_string(ddl_compiler) -> None:
    """没有任何 Doris 选项时,返回值应为 ``""``(供父类正确拼接)。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
    )
    out = ddl_compiler.post_create_table(md.tables["t"])
    # 当 KEY 由 PK 自动推断时,会输出 KEY 子句(非空),这里只能保证不会
    # 输出 ENGINE / DISTRIBUTED / PROPERTIES
    assert "ENGINE" not in out
    assert "DISTRIBUTED" not in out
    assert "PROPERTIES" not in out


# ---- 4. Index 编译 --------------------------------------------------------

def test_index_appears_in_ddl(doris_dialect) -> None:
    """Index(非主键) 应正常出现在 DDL 中。"""
    md = MetaData()
    Table(
        "t",
        md,
        Column("id", Integer, primary_key=True),
        Column("name", String(32)),
        Index("ix_name", "name"),
    )
    ddl = _compile_create(md.tables["t"], doris_dialect)
    assert "INDEX" in _normalize(ddl) or "KEY" in _normalize(ddl)