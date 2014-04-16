#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='pysub',
    version='0.1.0',
    description='Subtitle downloader written in python, using opensubtitles.com API',
    long_description=readme + '\n\n' + history,
    author='Nikola Kovacevic',
    author_email='nikolak@outlook.com',
    url='https://github.com/nikola-k/pysub',
    packages=[
        'pysub',
    ],
    package_dir={'pysub': 'pysub'},
    include_package_data=True,
    install_requires=["guessit==0.7.1",
    ],
    entry_points={
        'console_scripts': [
            'pysub = pysub.pysub:main',
        ],
    },
    license="Apache Software License",
    zip_safe=False,
    keywords='pysub',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2 :: Only',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Environment :: Console'
    ],
    test_suite='tests',
)