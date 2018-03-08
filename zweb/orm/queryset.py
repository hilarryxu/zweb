# -*- coding: utf-8 -*-

from operator import itemgetter

itemgetter0 = itemgetter(0)


class QuerySet(object):
    def __init__(self, query_type='SELECT *', args=(), conditions={},
                 model=None, using=None, db_table=None):
        self.query_type = query_type
        self.order = ''
        self.limit = []
        self.where_params = []
        self.where_values = []
        self._result_cache = None

        self.db_table = db_table
        self.model = model
        if using:
            self._db = using
        elif self.model:
            self._db = self.model._db
        self.filter(*args, **conditions)

    def filter(self, *args, **kwargs):
        if args:
            self.where_params.append(args[0])
            self.where_values.extend(args[1:])

        for k, v in kwargs.iteritems():
            if v is None:
                self.where_params.append('`%s` is NULL' % k)
            else:
                self.where_params.append([k, v, None])
                self.where_values.append(v)
        return self

    def order_by(self, *args):
        out = []
        for e in args:
            if e[0] == '-':
                e = '%s DESC' % e[1:]
            out.append(e)
        if out:
            self.order = ','.join(out)
        return self

    def _build_where(self):
        where = None
        where_clauses = []
        for e in self.where_params:
            if isinstance(e, (list, tuple)) and len(e) == 3:
                where_clauses.append('`%s`=%%s' % e[0])
            else:
                where_clauses.append(e)
        if where_clauses:
            where = ' AND '.join(where_clauses)
        return where

    def _values(self):
        return self.where_values

    def _limit(self):
        if len(self.limit):
            return 'LIMIT %s' % ','.join(str(l) for l in self.limit)

    def _db_table(self):
        if self.db_table:
            return self.db_table
        return self.model._meta.db_table

    def count(self, what='*'):
        q = 'SELECT COUNT(%s) AS cnt FROM %s' % (what, self._db_table())
        where = self._build_where()
        if where:
            q += ' WHERE ' + where
        values = self._values()
        cnt = self._db.get(q, *values)['cnt']
        return cnt

    def delete(self, delete_table=False):
        where = self._build_where()
        if where or delete_table:
            q = 'DELETE FROM %s' % self._db_table()
            if where:
                q += ' WHERE ' + where
            values = self._values()
            self._db.delete(q, *values)

    def update(self, *args, **kwds):
        update_set = []
        if args:
            update_set.append(args[0])
            self.where_values = args[1:] + self.where_values
        if kwds:
            update_set.append(
                ','.join(
                    '`%s`=%%s' % k for k in kwds.keys()
                )
            )
            self.where_values = list(kwds.values()) + self.where_values
        if update_set:
            q = 'UPDATE %s SET %s' % (
                self._db_table(),
                ','.join(update_set)
            )
            where = self._build_where()
            if where:
                q += ' WHERE ' + where
            values = self._values()
            self._db.update(q, *values)

    def set_fields(self, fields):
        self.query_type='SELECT %s' % fields

    def set_limits(self, limit=None, offset=None):
        self.limit = []
        if limit is not None:
            if offset is not None:
                self.limit.append(offset)
            self.limit.append(limit)

    def _query(self):
        q = '%s FROM %s' % (
            self.query_type,
            self._db_table()
        )
        where = self._build_where()
        if where:
            q += ' WHERE ' + where
        if self.order:
            q += ' ORDER BY ' + self.order
        _limit = self._limit()
        if _limit:
            q += ' ' + _limit

        values = self._values()
        return self._db.query(q, *values)

    def column(self, column='*', limit=None, offset=None):
        self.query_type = 'SELECT %s' % column
        self.set_limits(limit, offset)
        return self._query()

    def iterator(self, column='*', limit=None, offset=None):
        for row in self.column(column=column, limit=limit, offset=offset):
            obj = self.model(**row)
            obj.__dict__['_is_new'] = False
            yield obj

    def _fetch_all(self):
        if self._result_cache is None:
            self._result_cache = self._query()

    def __len__(self):
        self._fetch_all()
        return len(self._result_cache)

    def __iter__(self):
        self._fetch_all()
        return iter(self._result_cache)
