# -*- coding: utf-8 -*-

import urlparse
import urllib
from contextlib import contextmanager

from .util import Row

_databases = {}


class UnknownDB(Exception):
    pass


class DB(object):
    def __init__(self, db_module, keywords):
        keywords.pop('driver', None)
        self.db_module = db_module
        self.keywords = keywords
        self._db = self._connect(self.keywords)

    def _connect(self, keywords):
        return self.db_module.connect(**keywords)

    def _cursor(self):
        return self._db.cursor()

    def get(self, sql, *args):
        rows = self.query(sql, *args)
        if not rows:
            return None
        elif len(rows) > 1:
            raise Exception("Multiple rows returned for Database.get() query")
        else:
            return rows[0]

    def query(self, sql, *args):
        cursor = self._cursor()
        try:
            self._execute(cursor, sql, *args)
            column_names = [d[0] for d in cursor.description]
            return [Row(zip(column_names, row)) for row in cursor]
        finally:
            cursor.close()

    def insert(self, sql, *args):
        cursor = self._cursor()
        self._execute(cursor, sql, *args)
        cursor.connection.commit()
        return cursor.lastrowid

    def _execute_rowcount(self, sql, *args):
        cursor = self._cursor()
        self._execute(cursor, sql, *args)
        cursor.connection.commit()
        return cursor.rowcount

    update = delete = _execute_rowcount

    def _execute(self, cursor, sql, *args):
        # TODO: paramstyle?
        sql = sql.replace('%s', '?')
        return cursor.execute(sql, args)

    @contextmanager
    def manage_cursor(self, commit=True):
        cursor = self._cursor()
        try:
            yield cursor
        except Exception:
            if commit:
                cursor.connection.rollback()
            raise
        else:
            if commit:
                cursor.connection.commit()


class SqliteDB(DB):
    def __init__(self, **keywords):
        import sqlite3
        db = sqlite3
        keywords.setdefault('detect_types', db.PARSE_DECLTYPES)

        self.dbn = 'sqlite'
        self.paramstyle = db.paramstyle
        keywords['database'] = keywords.pop('db')
        super(SqliteDB, self).__init__(db, keywords)


def dburl2dict(url):
    """
    Takes a URL to a database and parses it into an equivalent dictionary.
    """
    parts = urlparse.urlparse(urllib.unquote(url))

    return {'dbn': parts.scheme,
            'user': parts.username,
            'pw': parts.password,
            'db': parts.path[1:],
            'host': parts.hostname,
            'port': parts.port}


def database(dburl=None, **params):
    if dburl:
        params = dburl2dict(dburl)

    dbn = params.pop('dbn')

    if dbn == 'torndb':
        from . import torndb
        params['database'] = params.pop('db')
        params['password'] = params.pop('pw', None)
        return torndb.Connection(**params)
    if dbn in _databases:
        return _databases[dbn](**params)
    else:
        raise UnknownDB(dbn)


def register_database(name, clazz):
    _databases[name] = clazz


register_database('sqlite', SqliteDB)
