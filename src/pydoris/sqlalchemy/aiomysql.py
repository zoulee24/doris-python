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

r"""
.. dialect:: doris+aiomysql
    :name: Doris via aiomysql
    :dbapi: aiomysql
    :connectstring: doris+aiomysql://user:password@host:port/dbname[?key=value&key=value...]

The aiomysql dialect for Doris mirrors SQLAlchemy's
:ref:`mysql+aiomysql <dialect.mysql.aiomysql>` dialect and re-uses the same
asyncio mediation layer.  It should normally be used with
:func:`_asyncio.create_async_engine`::

    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        "doris+aiomysql://user:pass@hostname:9030/dbname?charset=utf8mb4"
    )
"""  # noqa: E501

from sqlalchemy.dialects.mysql.aiomysql import MySQLDialect_aiomysql

from .dialect import DorisDialect_base


class DorisDialect_aiomysql(DorisDialect_base, MySQLDialect_aiomysql):
    """Doris dialect using the ``aiomysql`` async driver."""


dialect = MySQLDialect_aiomysql
