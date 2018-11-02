#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import re
from setuptools import setup, find_packages

kwargs = {}

with io.open('README.rst', 'rt', encoding='utf8') as f:
    readme = f.read()

with io.open('zweb/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r"__version__ = \'(.*?)\'", f.read()).group(1)

classes = """
    Development Status :: 4 - Beta
    Environment :: Web Environment
    Framework :: Tornado
    Intended Audience :: Developers
    License :: OSI Approved :: BSD License
    Operating System :: OS Independent
    Programming Language :: Python
    Programming Language :: Python :: 2
    Programming Language :: Python :: 2.7
    Programming Language :: Python :: Implementation :: CPython
    Topic :: Internet :: WWW/HTTP
"""
classifiers = [s.strip() for s in classes.split('\n') if s]

setup(
    name='zweb',
    version=version,
    description='A web framework for tornado',
    long_description=readme,
    author='Larry Xu',
    author_email='hilarryxu@gmail.com',
    url='https://github.com/hilarryxu/zweb',
    license='BSD',
    packages=find_packages(exclude=['test*', 'docs', 'examples']),
    include_package_data=True,
    classifiers=classifiers,
    **kwargs
)
