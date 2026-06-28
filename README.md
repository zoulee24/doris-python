# doris-python

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![SQLAlchemy 2.x](https://img.shields.io/badge/SQLAlchemy-2.x-orange)](https://docs.sqlalchemy.org/en/20/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

> **Apache Doris 的 SQLAlchemy 2.x 方言。**
> `doris-python` 提供 Doris 专属的 SQLAlchemy 方言，支持同步与异步驱动，
> 可直接通过 `pip install doris-python` 安装，并自动注册 `doris://` 系列 URL。

---

## 项目定位

`doris-python` 是一个**独立维护**的 SQLAlchemy 方言包，方言源码就在本仓库的
[`src/doris_python/sqlalchemy/`](src/doris_python/sqlalchemy) 目录下。

> ⚠️ **本仓库不依赖**任何名为 `pydoris` 的 PyPI 包，也没有把 `pydoris` 列为
> 运行时依赖。方言源码借鉴自 Apache Doris 官方仓库下的
> [`samples/doris-python/pydoris`](https://github.com/apache/doris/tree/master/samples/doris-python/pydoris)
> 目录，但已在 `doris_python.*` 命名空间下独立迭代与扩展，与上游**已经脱钩**。

| 角色 | 仓库 | 作用 |
| --- | --- | --- |
| 借鉴来源 | [`apache/doris/samples/doris-python/pydoris`](https://github.com/apache/doris/tree/master/samples/doris-python/pydoris) | 早期方言实现的灵感来源 |
| **本仓库** `doris-python` | [zoulee24/doris-python](https://github.com/zoulee24/doris-python) | 独立维护、扩展、打包并发布到 PyPI |

> 安装 `doris-python` **不会**拉取 `pydoris` 包；用户只需使用标准
> `doris://` / `doris+pymysql://` 等 URL 即可连接 Apache Doris。
> 如果你已经安装了 `pydoris`，建议卸载以避免 SQLAlchemy entry-points 冲突。

---

## 功能特性

- ✅ **多驱动支持**：`mysqldb` / `pymysql` / `aiomysql` / `asyncmy`
- ✅ **同步与异步**：兼容 SQLAlchemy 2.x 同步 API 与 `asyncio` 异步 API
- ✅ **自动方言注册**：通过 `entry-points` 自动暴露 `doris://` 系列 URL
- ✅ **Doris 专用类型**：`TINYINT`、`LARGEINT`、`HLL`、`BITMAP`、`QUANTILE_STATE`、
  `AGG_STATE`、`ARRAY`、`MAP`、`STRUCT`、`IPV4`、`IPV6`、`TIME`、`VARIANT`
- ✅ **三种 KEY 模型**：DDL 编译器内置 `DUPLICATE KEY` / `UNIQUE KEY` /
  `AGGREGATE KEY`，支持 `ENGINE` / `DISTRIBUTED BY ... BUCKETS N` /
  `PARTITION BY` / `PROPERTIES`
- ✅ **Doris 专属 DDL 处理**：自动剔除 `AUTO_INCREMENT`、`PRIMARY KEY`、
  `FOREIGN KEY`、`UNIQUE` 等 Doris 不支持的约束
- ✅ **PyPI 标准打包**：可直接 `pip install doris-python`

---

## 安装

```bash
pip install doris-python
```

### 开发安装

```bash
cd /path/to/doris-python
pip install -e ".[dev]"
# 或使用 uv（推荐）
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
from sqlalchemy import Column, Integer, String, declarative_base

# 注意：类型与方言都来自 doris_python，不依赖 pydoris
from doris_python.sqlalchemy.datatype import TINYINT, LARGEINT, HLL

Base = declarative_base()


class UserEvent(Base):
    __tablename__ = "user_event"

    # Doris 专属 Table 选项（参考 src/doris_python/sqlalchemy/dialect.py
    # 中 DorisDDLCompiler.post_create_table 的实现）
    __table_args__ = {
        "doris_engine": "OLAP",
        "doris_key_type": "DUPLICATE",
        "doris_key_columns": ["event_id"],
        "doris_distributed_by": "HASH(`event_id`)",
        "doris_buckets": 16,
        "doris_properties": {
            "replication_num": "3",
            "storage_medium": "SSD",
        },
    }

    event_id = Column(LARGEINT, primary_key=True)
    user_id  = Column(Integer)
    flag     = Column(TINYINT)
    profile  = Column(HLL)
```

> 上面生成的 DDL 大致为：
> ```sql
> CREATE TABLE user_event (
>   event_id LARGEINT NOT NULL,
>   user_id  INT NOT NULL,
>   flag     TINYINT NOT NULL,
>   profile  HLL NOT NULL
> )
> ENGINE = OLAP
> DUPLICATE KEY(`event_id`)
> DISTRIBUTED BY HASH(`event_id`) BUCKETS 16
> PROPERTIES ("replication_num" = "3", "storage_medium" = "SSD")
> ```

---

## 支持的 URL Schemes

| URL | 驱动 | 同步/异步 |
| --- | --- | --- |
| `doris://` / `doris+mysqldb://` | mysqlclient | 同步 |
| `doris+pymysql://` | PyMySQL | 同步 |
| `doris+aiomysql://` | aiomysql | 异步 |
| `doris+asyncmy://` | asyncmy | 异步 |

> 默认端口 `9030`（Doris FE 查询端口）。

---

## 开发

```bash
# 克隆仓库
git clone https://github.com/zoulee24/doris-python.git
cd doris-python

# 使用 uv（推荐）
uv sync --extra dev

# 或使用 pip
pip install -e ".[dev]"

# 单元测试（默认，无需数据库）
pytest

# 单元测试 + 集成测试（需要真实 Doris）
pytest --run-integration

# 代码风格
ruff check .
ruff format .
```

测试约定：
- 默认 `pytest` **只跑单元测试**（约 102 个），不需要任何外部依赖；
- `pytest --run-integration` 会额外跑 4 个需要真实 Doris 实例的连通性测试，
  配置从项目根目录的 `.env` 文件读取（参见 [`.env.example`](.env.example)）。

---

## 路线图

- [x] 单元测试覆盖：方言注册、类型映射、DDL 编译
- [x] GitHub Actions：lint + pytest
- [x] GitHub Actions：tag 触发打包并发布到 PyPI
- [x] 动态版本号（从 git tag 读取）
- [ ] 补充方言反射（reflection）相关单元测试
- [ ] CI 多 Python 版本矩阵（3.9 / 3.10 / 3.11 / 3.12 / 3.13）

---

## 许可证

本项目遵循 [**Apache License 2.0**](http://www.apache.org/licenses/LICENSE-2.0)

## 致谢

- [Apache Doris](https://doris.apache.org/) — 实时分析型数据库
- [SQLAlchemy](https://www.sqlalchemy.org/) — Python SQL 工具包与 ORM
- 方言实现的早期版本借鉴自
  [`apache/doris/samples/doris-python/pydoris`](https://github.com/apache/doris/tree/master/samples/doris-python/pydoris)