#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect

from .util import safestr, safeunicode
from .config import db_by_table
from .queryset import QuerySet, itemgetter0

missing = object()


class _Model(type):
    def __new__(cls, name, bases, attrs):
        base0 = bases[0]
        if base0 is object:
            # If cls is Model, not handle it.
            return super(_Model, cls).__new__(cls, name, bases, attrs)

        module = attrs.pop('__module__')
        new_class = type.__new__(cls, name, bases, {'__module__': module})

        attr_meta = attrs.pop('Meta', None)
        if not attr_meta:
            # Use cls parent's Meta
            meta = getattr(new_class, 'Meta', None)
        else:
            # Use cls's Meta
            meta = attr_meta

        meta_defaults = {
            'abstract': False,
            'pk': 'id',
            'db_table': name.lower(),
        }
        for k, v in meta_defaults.items():
            if not hasattr(meta, k):
                setattr(meta, k, v)

        new_class.add_to_class('_meta', meta)
        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)

        abstract = getattr(meta, 'abstract', False)
        if not abstract:
            table_name = getattr(meta, 'db_table', None)
            db = db_by_table(table_name)
            new_class.add_to_class('_db', db)

            cursor = db._cursor()
            try:
                cursor.execute('SELECT * FROM %s LIMIT 1' % table_name, ())
                new_class.add_to_class('_columns', map(itemgetter0, cursor.description))
            finally:
                cursor.close()

            new_class._prepare()

        return new_class

    def add_to_class(cls, name, value):
        if not inspect.isclass(value) and hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def _prepare(cls):
        manager = Manager()
        manager.auto_created = True
        cls.add_to_class('objects', manager)


class Model(object):
    __metaclass__ = _Model

    class Meta(object):
        _model_cls_name = 'Model'

    def __init__(self, **kwargs):
        self.__dict__['_is_new'] = True
        for k, v in kwargs.iteritems():
            self.__dict__[k] = v
        self.__dict__['_updated'] = set()

    def __setattr__(self, name, value):
        dc = self.__dict__
        if name[0] != '_' and name in self._columns:
            if self._is_new:
                dc[name] = value
                return
            dc_value = dc[name]
            if dc_value is None:
                self._updated.add(name)
            else:
                if value is not None:
                    if isinstance(dc_value, unicode):
                        value = safeunicode(value)
                    elif isinstance(dc_value, str):
                        value = safestr(value)
                    else:
                        value = type(dc_value)(value)
                if dc_value != value:
                    self._updated.add(name)
            dc[name] = value
        else:
            attr = getattr(self.__class__, name, missing)
            if attr is not missing and hasattr(attr, 'fset'):
                attr.fset(self, value)
            else:
                dc[name] = value

    def is_new(self):
        return self._is_new

    def pk_val(self):
        return getattr(self, self._meta.pk, None)

    def to_dict(self, include=None, exclude=None):
        out = {}
        keys = self._columns or []
        fields = (set(include or keys) - set(exclude or []))
        for k in fields:
            if hasattr(self, k):
                out[k] = getattr(self, k)
        return out

    def save(self):
        if self._is_new:
            self._insert()
            self._is_new = False
        elif self._updated:
            self._update()
        self._updated.clear()
        return self

    def delete(self):
        opts = self._meta
        self._db.delete(
            'DELETE FROM %s WHERE %s=%%s LIMIT 1' % (opts.db_table, opts.pk),
            self.pk_val()
        )

    def _insert(self):
        opts = self._meta
        pk_name = opts.pk
        pk_val = self.pk_val()
        col_names = [
            f for f in self._columns
            if pk_val is not None or f != pk_name
        ]

        fields = []
        values = []
        for k in col_names:
            v = getattr(self, k, missing)
            if v is not missing:
                fields.append('`%s`' % k)
                values.append(v)

        query = 'INSERT INTO %s (%s) VALUES (%s)' % (
               opts.db_table,
               ','.join(fields),
               ','.join(['%s'] * len(fields))
        )
        last_id = self._db.insert(query, *values)

        if pk_val is None:
            setattr(self, pk_name, last_id)

    def _update(self):
        opts = self._meta
        query = [
            'UPDATE %s SET' % opts.db_table,
            ','.join(['`%s`=%%s' % f for f in self._updated]),
            'WHERE %s=%%s LIMIT 1' % opts.pk
        ]

        values = [getattr(self, f) for f in self._updated]
        values.append(self.pk_val())

        self._db.update(' '.join(query), *values)


class Manager(object):
    def __init__(self):
        self.model = None
        self.name = None
        self._db = None

    def contribute_to_class(self, model, name):
        if not self.name:
            self.name = name
        self.model = model
        self._db = self.model._db
        setattr(model, name, self)

    def get(self, arg_pk=None, **kwargs):
        opts = self.model._meta
        if arg_pk is None:
            if not kwargs:
                return
        else:
            kwargs = {
                opts.pk: arg_pk
            }

        qs = QuerySet(model=self.model, conditions=kwargs)
        rows = qs.column(limit=1)
        if rows:
            row = rows[0]
            obj = self.model(**row)
            obj.__dict__['_is_new'] = False
            return obj

    def get_or_create(self, **kwargs):
        _save = kwargs.pop('_save', True)
        defaults = kwargs.pop('defaults', {})
        ins = self.get(**kwargs)
        if ins is None:
            params = dict([(k, v) for k, v in kwargs.iteritems() if '__' not in k])
            params.update(defaults)
            ins = self.model(**params)
            if _save:
                ins.save()
        return ins

    def all(self, *args, **kwargs):
        return QuerySet(model=self.model)

    def filter(self, *args, **kwargs):
        return QuerySet(
            model=self.model,
            args=args,
            conditions=kwargs
        )
