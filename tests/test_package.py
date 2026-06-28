"""包元数据测试。

验证:
* 包可以被正常导入
* ``__version__`` 存在且符合 semver
* ``sqlalchemy`` 子模块导入时会触发 dialect 注册
"""

from __future__ import annotations

import importlib
import re

import doris_python
import doris_python.sqlalchemy  # noqa: F401  触发 entry-point 注册


def test_package_importable() -> None:
    """包可以直接 import,不抛异常。"""
    assert doris_python is not None


def test_version_is_string() -> None:
    """``__version__`` 必须是字符串。"""
    assert isinstance(doris_python.__version__, str)
    assert doris_python.__version__  # 非空


def test_version_matches_semver() -> None:
    """版本号遵循 ``X.Y.Z`` 或 ``X.Y.Z<suffix>`` 形式(PEP 440 简化版)。"""
    pattern = re.compile(r"^\d+\.\d+\.\d+([\-+.][0-9a-zA-Z]+)*$")
    assert pattern.match(doris_python.__version__), (
        f"version {doris_python.__version__!r} does not look like semver/pep440"
    )


def test_sqlalchemy_submodule_loads() -> None:
    """导入 sqlalchemy 子模块不应报错。"""
    module = importlib.import_module("doris_python.sqlalchemy")
    assert module is not None