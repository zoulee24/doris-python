# doris-python

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-orange)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

> **Supplementary packaging for [`pydoris`](https://github.com/apache/doris/tree/master/samples/doris-python/pydoris).**
> `doris-python` 提供统一的 SQLAlchemy 方言入口，并将其打包为符合 PyPI 规范的发行版，便于安装、版本管理与下游依赖锁定。

---

## 项目定位

`doris-python` 不是 `pydoris` 的替代品，而是它的 **补充与分发层**：

| 角色 | 仓库 | 作用 |
| --- | --- | --- |
| 核心方言实现 | [`apache/doris` 仓库下的 `samples/doris-python/pydoris`](https://github.com/apache/doris/tree/master/samples/doris-python/pydoris) | 提供 Doris 方言源码（由 Apache Doris 官方维护） |
| **本仓库** `doris-python` | 当前仓库 | 在 `pydoris` 基础上补齐 PyPI 打包配置（`pyproject.toml`）、入口点声明、测试与文档，让其可直接 `pip install` |

> 本仓库通过 `pip install doris-python` 安装 `pydoris` 包，并自动注册 SQLAlchemy 方言入口点。
> 使用方**无需**关心 `pydoris` 内部细节，只需使用标准的 SQLAlchemy URL 即可连接 Apache Doris。

---

## 功能特性

- ✅ **多驱动支持**：`mysqldb` / `pymysql` / `aiomysql` / `asyncmy`
- ✅ **同步与异步**：兼容 SQLAlchemy 2.x 同步 API 与 `asyncio` 异步 API
- ✅ **自动方言注册**：通过 `entry-points` 自动暴露 `doris://` 系列 URL
- ✅ **Doris 专用类型**：`HLL`、`BITMAP`、`QUANTILE_STATE`、`AGG_STATE`、`ARRAY`、`MAP`、`STRUCT`、`IPV4`、`IPV6` 等
- ✅ **Unique Key / Duplicate Key 模型**：DDL 编译器内置 `UNIQUE KEY` / `DUPLICATE KEY` / 分桶 DDL 模板
- ✅ **PyPI 标准打包**：可直接 `pip install doris-python`

---

## 安装

```bash
pip install doris-python
```


### 开发安装

```bash
cd /path/to/doris-python
pip install -e .[dev]
# using uv
uv sync --extra dev
```

---

## 快速开始

### 同步示例（SQLAlchemy 2.x）

```python
from sqlalchemy import create_engine, text

engine = create_engine(
    "doris+pymysql://user:password@host:9030/demo",
    pool_size=10,
    pool_recycle=3600,
)

with engine.connect() as conn:
    result = conn.execute(text("SELECT VERSION()"))
    print(result.scalar())
```

### 异步示例（asyncio）

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine(
    "doris+asyncmy://user:password@host:9030/demo",
)

async with engine.connect() as conn:
    result = await conn.execute(text("SELECT VERSION()"))
    print(result.scalar())
```

### ORM 模型示例（包含 Doris 特有语法）

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from pydoris.sqlalchemy.datatype import TINYINT, LARGEINT, HLL

Base = declarative_base()

class UserEvent(Base):
    __tablename__ = "user_event"
    __table_args__ = {
        "doris_properties": {
            "unique_key": "event_id",
            "distributed_by": "HASH(event_id) BUCKETS 16",
        }
    }

    event_id = Column(LARGEINT, primary_key=True)
    user_id  = Column(Integer)
    flag     = Column(TINYINT)
    profile  = Column(HLL)
```

---

## 支持的 URL Schemes

| URL | 驱动 | 同步/异步 |
| --- | --- | --- |
| `doris://` / `doris+mysqldb://` | mysqlclient | 同步 |
| `doris+pymysql://` | PyMySQL | 同步 |
| `doris+aiomysql://` | aiomysql | 异步 |
| `doris+asyncmy://` | asyncmy | 异步 |

> 默认端口 `9030`（Doris FE 查询端口），9030 用于查询，8030 用于 HTTP。

---

## 与上游 `pydoris` 的关系

```
┌──────────────────────────────────────────────┐
│           Apache Doris 官方仓库               │
│  samples/doris-python/pydoris/                │
│  ┌────────────────────────────────────────┐   │
│  │  pydoris/                              │   │
│  │   ├─ sqlalchemy/                       │   │
│  │   │   ├─ dialect.py     ← 方言核心      │   │
│  │   │   ├─ datatype.py    ← Doris 类型   │   │
│  │   │   ├─ pymysql.py                    │   │
│  │   │   ├─ aiomysql.py                   │   │
│  │   │   └─ asyncmy.py                    │   │
│  └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
                     ▲
                     │ 源码同步
                     │
┌──────────────────────────────────────────────┐
│         本仓库：doris-python                  │
│  - 同步 pydoris 源码                          │
│  - 添加 pyproject.toml（PEP 621 标准）         │
│  - 注册 SQLAlchemy entry-points              │
│  - 维护 README 与单元测试                      │
│  - 发布至 PyPI（pip install doris-python）    │
└──────────────────────────────────────────────┘
```

- **上游**：方言源码由 [`apache/doris`](https://github.com/apache/doris) 维护，新特性、bug fix 应优先提交到上游。
- **本仓库**：聚焦于发布工程（packaging）、依赖管理、测试基础设施，方便终端用户开箱即用。

---

## 开发

```bash
# 克隆仓库
git clone https://github.com/<your-org>/doris-python.git
cd doris-python

# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e ".[dev]"

# 运行测试
pytest

# 代码风格
ruff check .
ruff format .
```

---

## 路线图

- [ ] 与上游 `pydoris` 建立自动化同步机制
- [ ] 补充方言反射（reflection）相关单元测试
- [ ] GitHub Actions CI：lint + pytest + 多 Python 版本矩阵
- [ ] 发布至 PyPI

---

## 许可证

本项目遵循 **Apache License 2.0**，与上游 `pydoris` 及 Apache Doris 保持一致。

## 致谢

- [Apache Doris](https://doris.apache.org/) — 实时分析型数据库
- [`pydoris`](https://github.com/apache/doris/tree/master/samples/doris-python/pydoris) — 上游方言实现
- [SQLAlchemy](https://www.sqlalchemy.org/) — Python SQL 工具包与 ORM