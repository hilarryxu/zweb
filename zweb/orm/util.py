# -*- coding: utf-8 -*-

from zweb._compat import PY2, unicode_type

_UTF8_TYPES = (bytes, type(None))
_TO_UNICODE_TYPES = (unicode_type, type(None))


def safeunicode(value, encoding='utf-8'):
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    if isinstance(value, bytes):
        return value.decode(encoding)
    return unicode_type(value)


def safestr(value, encoding='utf-8'):
    # FIXME: mix native_str,to_basestring?
    # Just for print, %, strnig.format
    if value is None:
        return value
    if isinstance(value, bytes):
        if PY2:
            return value
        else:
            return value.decode(encoding)
    if isinstance(value, unicode_type):
        return value.encode(encoding)
    return str(value)


class Row(dict):
    """A dict that allows for object-like property access syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
