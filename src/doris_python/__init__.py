#! /usr/bin/python3

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
try:
    # 由 setuptools-scm 在打包时根据 git tag 自动生成
    from ._version import version as __version__  # noqa: F401
except ImportError:
    # 本地开发或未安装包时回退到静态版本
    __version__ = "0.0.0+local"

# Register SQLAlchemy dialects (``doris://``, ``doris+aiomysql://`` etc.).
# Importing this module must register the entry points for the
# ``doris`` dialect to be discoverable by ``create_engine`` /
# ``create_async_engine``.
from . import sqlalchemy  # noqa: E402, F401
