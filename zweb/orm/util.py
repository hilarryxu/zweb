# -*- coding: utf-8 -*-

from tornado.escape import utf8, to_unicode


def safeunicode(obj, encoding='utf-8'):
    return to_unicode(obj)


def safestr(obj, encoding='utf-8'):
    return utf8(obj)


class Row(dict):
    """A dict that allows for object-like property access syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
