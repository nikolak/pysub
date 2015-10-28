#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pysub

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.md').read()
history = open('CHANGELOG.md').read()

setup(
    name='pysub',
    version=pysub.__version__,
    description='Subtitle downloader written in python, using opensubtitles.com API',
    long_description=readme + '\n\n' + history,
    author='Nikola Kovacevic',
    author_email='nikolak@outlook.com',
    url='https://github.com/nikola-k/pysub',
    packages=[
        'pysub',
        'pysub.pysub_objects',
    ],
    package_dir={'pysub': 'pysub'},
    include_package_data=True,
    install_requires=["guessit==0.11.0",
                      "appdirs==1.4.0"
    ],
    entry_points={
        'console_scripts': [
            'pysub = pysub.pysub:main',
            'pysub-ui = pysub.pysub_ui:main'
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
        'Environment :: Console',
        'Environment :: X11 Applications'
    ],
    test_suite='tests',
)
