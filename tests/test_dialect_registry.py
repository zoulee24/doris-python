"""Dialect 注册测试。

验证 ``doris_python.sqlalchemy`` 通过 ``registry.register`` 注册的
所有 URL scheme 都能被 SQLAlchemy 正确解析并加载到对应的 dialect 类。
"""

from __future__ import annotations

import pytest
from sqlalchemy.dialects import registry

# 必填依赖,缺少时优雅地跳过本文件所有测试
pytest.importorskip("doris_python.sqlalchemy")


# (URL 前缀, 期望的 dialect 类全限定名)
EXPECTED_DIALECTS: list[tuple[str, str]] = [
    ("doris", "doris_python.sqlalchemy.dialect.DorisDialect_mysqldb"),
    ("doris.mysqldb", "doris_python.sqlalchemy.dialect.DorisDialect_mysqldb"),
    ("doris.pymysql", "doris_python.sqlalchemy.pymysql.DorisDialect_pymysql"),
    ("doris.aiomysql", "doris_python.sqlalchemy.aiomysql.DorisDialect_aiomysql"),
    ("doris.asyncmy", "doris_python.sqlalchemy.asyncmy.DorisDialect_asyncmy"),
]


@pytest.mark.parametrize(("url_prefix", "expected_dotted"), EXPECTED_DIALECTS)
def test_registry_resolves(url_prefix: str, expected_dotted: str) -> None:
    """SQLAlchemy registry 能根据 URL 前缀加载到正确的 dialect 类。"""
    cls = registry.load(url_prefix)
    assert f"{cls.__module__}.{cls.__name__}" == expected_dotted


@pytest.mark.parametrize(
    "url",
    [
        "doris+pymysql://u:p@h:9030/db",
        "doris+aiomysql://u:p@h:9030/db",
    ],
)
def test_url_parse_yields_dialect(url: str) -> None:
    """从 URL 创建的 engine 应该使用 DorisDialect_base 的子类。

    只测能在本机装好的 DBAPI(pymysql/aiomysql);
    mysqldb 与 asyncmy 依赖系统库,在 CI 环境里未必安装。
    """
    pytest.importorskip(
        "pymysql" if "pymysql" in url else "aiomysql",
        reason=f"DBAPI for {url!r} is not installed",
    )
    from sqlalchemy import create_engine
    from doris_python.sqlalchemy.dialect import DorisDialect_base

    engine = create_engine(url)
    try:
        assert isinstance(engine.dialect, DorisDialect_base), (
            f"URL {url} produced {type(engine.dialect).__name__}, "
            "expected a DorisDialect_base subclass"
        )
    finally:
        engine.dispose()


def test_no_legacy_pydoris_module_path() -> None:
    """确保不再有指向 ``pydoris.*`` 的 registry 条目残留。"""
    # registry._entrypoints 在 SQLAlchemy >=2 内部存储已注册的 entry point
    # 我们无法直接拿到原始字符串,所以这里只验证: 所有可加载的 dialect 都
    # 来自 doris_python.* 模块,而不是 pydoris.*
    for url_prefix, _ in EXPECTED_DIALECTS:
        cls = registry.load(url_prefix)
        assert cls.__module__.startswith("doris_python."), (
            f"dialect for {url_prefix!r} is loaded from {cls.__module__!r}, "
            "expected doris_python.*"
        )