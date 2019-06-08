#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='nmeaserver',
    version='0.1',
    description='Python framework for a NMEA 0183 TCP Server inspired by Flask developer API',
    url='https://github.com/robonation/nmeaserver',
    author='Felix Pageau',
    author_email='pageau@robonation.org',
    license='Apache License 2.0',
    install_requires=['numpy'],
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    long_description=open('README.md').read(),
)