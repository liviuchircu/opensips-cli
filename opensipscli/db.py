#!/usr/bin/env python
##
## This file is part of OpenSIPS CLI
## (see https://github.com/OpenSIPS/opensips-cli).
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##

from opensipscli.logger import logger

try:
    import sqlalchemy
    import sqlalchemy_utils
    sqlalchemy_available = True
except ImportError:
    logger.info("sqlalchemy and sqlalchemy_utils are not available!")
    sqlalchemy_available = False

class osdbError(Exception):
    pass

class osdb(object):

    def get_dialect(url):
        return url.split('://')[0]

    def has_sqlalchemy():
        return sqlalchemy_available

    def has_dialect(dialect):
        # TODO: do this only for SQLAlchemy
        try:
            sqlalchemy.create_engine('{}://'.format(dialect))
        except sqlalchemy.exc.NoSuchModuleError:
            return False
        return True

    def __init__(self, db_url, db_name):
        self.db_url = db_url
        self.db_name = db_name
        self.dialect = osdb.get_dialect(db_url)
        self.conn = None

        # TODO: do this only for SQLAlchemy
        try:
            engine = sqlalchemy.create_engine(db_url)
            self.conn = engine.connect()
        except sqlalchemy.exc.OperationalError as se:
            logger.error("cannot connect to DB server: {}!".format(se))
            raise osdbError("unable to connect to the database") from None
        except sqlalchemy.exc.NoSuchModuleError as me:
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect)) from None

    def get_where(self, filter_keys):

        if filter_keys:
            where_str = ""
            for k, v in filter_keys.items():
                where_str += " AND {} = ".format(k)
                if type(v) == int:
                    where_str += v
                else:
                    where_str += "'{}'".format(
                            v.translate(str.maketrans({'\'': '\\\''})))
            if where_str != "":
                where_str = " WHERE " + where_str[5:]
        else:
            where_str = ""
        return where_str

    def exists(self):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            return False
        database_url = "{}/{}".format(self.db_url, self.db_name)
        try:
            if sqlalchemy_utils.database_exists(database_url):
                return True
        except sqlalchemy.exc.NoSuchModuleError as me:
            logger.error("cannot check if database {} exists: {}".
                    format(self.db_name, me))
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect)) from None
        return False

    def destroy(self):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            return
        self.conn.close()

    def drop(self):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
        database_url = "{}/{}".format(self.db_url, self.db_name)
        try:
            if sqlalchemy_utils.drop_database(database_url):
                return True
        except sqlalchemy.exc.NoSuchModuleError as me:
            logger.error("cannot check if database {} exists: {}".
                    format(self.db_name, me))
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect)) from None

    def create(self):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
        # all good - it's time to create the database
        self.conn.execute("CREATE DATABASE {}".format(self.db_name))

    def use(self):
        # TODO: do this only for SQLAlchemy
        self.conn.execute("USE {}".format(self.db_name))

    def create_module(self, import_file):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")

        with open(import_file, 'r') as f:
            try:
                self.conn.execute(f.read())
            except sqlalchemy.exc.IntegrityError as ie:
                raise osdbError("cannot deploy {} file: {}".
                        format(import_file, ie)) from None

    def find(self, table, fields, filter_keys):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
        if not fields:
            fields = ['*']
        elif type(fields) != list:
            fields = [ fields ]

        where_str = self.get_where(filter_keys)
        statement = "SELECT {} FROM {}{}".format(
                ", ".join(fields),
                table,
                where_str)
        try:
            result = self.conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return None
        return result

    def entry_exists(self, table, constraints):
        ret = self.find(table, "count(*)", constraints)
        if ret and ret.first()[0] != 0:
            return True
        return False

    def insert(self, table, keys):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")

        values = ""
        for v in keys.values():
            values += ", "
            if type(v) == int:
                values += v
            else:
                values += "'{}'".format(
                        v.translate(str.maketrans({'\'': '\\\''})))
        statement = "INSERT INTO {} ({}) VALUES ({})".format(
                table, ", ".join(keys.keys()), values[2:])
        try:
            result = self.conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return False
        return True

    def delete(self, table, filter_keys=None):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")

        where_str = self.get_where(filter_keys)
        statement = "DELETE FROM {}{}".format(table, where_str)
        try:
            result = self.conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return False
        return True

    def update(self, table, update_keys, filter_keys=None):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")

        update_str = ""
        for k, v in update_keys.items():
            update_str += ", {} = ".format(k)
            if type(v) == int:
                update_str += v
            else:
                update_str += "'{}'".format(
                        v.translate(str.maketrans({'\'': '\\\''})))
        where_str = self.get_where(filter_keys)
        statement = "UPDATE {} SET {}{}".format(table,
                update_str[2:], where_str)
        try:
            result = self.conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return False
        return True
