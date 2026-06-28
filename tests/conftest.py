"""共享 pytest fixtures 与配置。

设计原则
========

* **集成测试** (需真实 Doris):默认 *跳过*,仅当设置了 ``DORIS_HOST``
  等环境变量时才运行。CLI 调用::

      pytest                       # 只跑单元测试
      pytest --run-integration      # 同时跑需要数据库的测试

  也可以通过 pytest 直接::

      DORIS_HOST=... pytest --run-integration

* **单元测试** (纯逻辑,不需要数据库):永远运行。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# 加载项目根的 .env,这样 ``--run-integration`` 模式下无需手动 export
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def pytest_addoption(parser: pytest.Parser) -> None:
    """注册 ``--run-integration`` 选项。"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require a live Doris instance.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """默认跳过所有标记为 ``integration`` 的测试。"""
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(
        reason="integration test; pass --run-integration to enable (or set DORIS_HOST)"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture(scope="session")
def doris_env() -> dict[str, str]:
    """从环境变量读取 Doris 连接配置,缺失时自动跳过调用测试。"""
    required = ("DORIS_HOST", "DORIS_USER", "DORIS_PASSWORD", "DORIS_DATABASE")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        pytest.skip(f"missing required env vars: {', '.join(missing)}")
    return {
        "user": os.environ["DORIS_USER"],
        "password": os.environ["DORIS_PASSWORD"],
        "host": os.environ["DORIS_HOST"],
        "port": os.environ.get("DORIS_PORT", "9030"),
        "database": os.environ["DORIS_DATABASE"],
        "driver": os.environ.get("DORIS_DRIVER", "doris+pymysql"),
    }


@pytest.fixture(scope="session")
def doris_dsn(doris_env: dict[str, str]) -> str:
    """根据 ``doris_env`` 拼装 SQLAlchemy URL。"""
    return (
        f"{doris_env['driver']}://{doris_env['user']}:{doris_env['password']}"
        f"@{doris_env['host']}:{doris_env['port']}/{doris_env['database']}"
    )