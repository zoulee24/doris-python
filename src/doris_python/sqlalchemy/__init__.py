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
"""SQLAlchemy dialects for Apache Doris.

Registering these entry points lets users connect with any of the three
supported MySQL-wire drivers via the standard URL scheme::

    doris://                 # defaults to mysqlclient (mysqldb)
    doris+mysqldb://
    doris+pymysql://
    doris+aiomysql://        # asyncio
    doris+asyncmy://         # asyncio
"""

from sqlalchemy.dialects import registry

# Default sync dialect — kept for backwards compatibility with the original
# ``doris://`` URL form, which used the mysqlclient driver.
registry.register("doris", "doris_python.sqlalchemy.dialect", "DorisDialect_mysqldb")

# Sync drivers
registry.register("doris.mysqldb", "doris_python.sqlalchemy.dialect", "DorisDialect_mysqldb")
registry.register("doris.pymysql", "doris_python.sqlalchemy.pymysql", "DorisDialect_pymysql")

# Async drivers
registry.register("doris.aiomysql", "doris_python.sqlalchemy.aiomysql", "DorisDialect_aiomysql")
registry.register("doris.asyncmy", "doris_python.sqlalchemy.asyncmy", "DorisDialect_asyncmy")
