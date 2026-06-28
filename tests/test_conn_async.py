"""异步连通性测试 — 需要真实 Doris 实例。

驱动通过 ``DORIS_DRIVER`` 环境变量指定,可选:

* ``doris+aiomysql``
* ``doris+asyncmy``

默认是 ``doris+aiomysql``(与 ``.env.example`` 一致)。
测试同样只读 ``information_schema.columns`` 系统表。
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_connect_and_query(doris_env: dict[str, str]) -> None:
    """异步 engine 可连接并执行最简单的 SELECT。

    直接从 fixture 拼 DSN 而不是用 ``doris_dsn``,因为默认的
    ``doris_dsn`` 走同步驱动,我们要在异步测试里强行覆盖。
    """
    driver = doris_env["driver"]
    # 若用户配置了同步驱动,这里切换到默认的异步驱动
    if "+" not in driver or driver.endswith("pymysql") or driver.endswith("mysqldb"):
        driver = "doris+aiomysql"

    dsn = (
        f"{driver}://{doris_env['user']}:{doris_env['password']}"
        f"@{doris_env['host']}:{doris_env['port']}/{doris_env['database']}"
    )

    engine = create_async_engine(dsn)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME "
                     "FROM information_schema.columns LIMIT 1")
            )
            row = result.fetchone()
        assert row is not None, "information_schema.columns returned no rows"
        assert all(isinstance(v, str) for v in row)
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_engine_uses_doris_dialect(doris_env: dict[str, str]) -> None:
    """异步 engine 加载的 dialect 必须继承自 DorisDialect_base。"""
    from doris_python.sqlalchemy.dialect import DorisDialect_base

    driver = "doris+aiomysql"
    dsn = (
        f"{driver}://{doris_env['user']}:{doris_env['password']}"
        f"@{doris_env['host']}:{doris_env['port']}/{doris_env['database']}"
    )

    engine = create_async_engine(dsn)
    try:
        assert isinstance(engine.dialect, DorisDialect_base)
    finally:
        await engine.dispose()