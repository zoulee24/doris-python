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
.. dialect:: doris+mysqldb
    :name: Doris via PyMySQL
    :dbapi: mysqldb
    :connectstring: doris+mysqldb://user:password@host:port/dbname[?key=value&key=value...]
"""  # noqa: E501

from sqlalchemy.dialects.mysql.mysqldb import MySQLDialect_mysqldb

from .dialect import DorisDialect_base


class DorisDialect_mysqldb(DorisDialect_base, MySQLDialect_mysqldb):
    """Doris dialect using the ``mysqldb`` async driver."""


dialect = DorisDialect_mysqldb
