#!/usr/bin/env python
from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
exec(open(os.path.join(here, 'pyknp_eventgraph', '_version.py')).read())

setup(
    name='pyknp-eventgraph',
    version=__version__,
    description='Python module for building EventGraph from KNP result',
    author='Kurohashi-Kawahara Lab, Kyoto University',
    author_email='contact@nlp.ist.i.kyoto-u.ac.jp',
    license='BSD-3-Clause',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=['pyknp==0.4.1', 'graphviz==0.10.1'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'parameterized'],
    entry_points={
        'console_scripts': [
            'evg=pyknp_eventgraph.cli:build_eventgraph',
            'evgviz=pyknp_eventgraph.cli:visualize_eventgraph',
        ],
    }
)
