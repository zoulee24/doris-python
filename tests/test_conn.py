"""同步连通性测试 — 需要真实 Doris 实例。

运行方式::

    pytest --run-integration               # 从 .env 读取连接信息
    DORIS_HOST=... pytest --run-integration

测试只查询 ``information_schema.columns`` 系统表,无需业务数据;
任何标准 Doris 实例(1.x / 2.x / 3.x)都能通过。
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_sync_connect_and_query(doris_dsn: str) -> None:
    """同步 engine 可连接并执行最简单的 SELECT。"""
    engine = create_engine(doris_dsn)
    try:
        with engine.connect() as conn:
            # LIMIT 1 保证只读一行,且对所有 Doris 版本都兼容
            result = conn.execute(
                text("SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME "
                     "FROM information_schema.columns LIMIT 1")
            )
            row = result.fetchone()
        assert row is not None, "information_schema.columns returned no rows"
        # 三列均应能取到字符串值
        assert all(isinstance(v, str) for v in row)
    finally:
        engine.dispose()


@pytest.mark.integration
def test_sync_engine_uses_doris_dialect(doris_dsn: str) -> None:
    """同步 engine 加载的 dialect 必须是 DorisDialect_base 的子类。"""
    from doris_python.sqlalchemy.dialect import DorisDialect_base

    engine = create_engine(doris_dsn)
    try:
        assert isinstance(engine.dialect, DorisDialect_base)
    finally:
        engine.dispose()
