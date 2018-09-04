#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='zweb',
    version='0.1.1',
    description='zweb',
    long_description='zweb',
    author='Larry Xu',
    author_email='hilarryxu@gmail.com',
    url='http://www.hilarryxu.com/p/zweb',
    packages=find_packages(exclude=('test*', 'docs', 'examples')),
    include_package_data=True,
    license='MIT',
    zip_safe=False,
    test_suite='tests'
)
