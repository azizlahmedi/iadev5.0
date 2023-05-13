# -*- coding: utf-8 -*-
import os

# allow setup.py to be run from any path
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    import setuptools
except ImportError:
    import ez_setup

    ez_setup.use_setuptools()
from setuptools import setup, find_packages


setup(
    name='neoxam',
    version='1.0',
    description='NeoXam development tools',
    url='http://iadev-tools/',
    author='NeoXam',
    author_email='olivier.mansion@neoxam.com',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'neoxam = manage:main',
            'fab = fabric.main:main',
        ],
    },
    
)
