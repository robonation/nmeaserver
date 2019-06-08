#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='nmeaserver',
    version='0.1',
    description='Python framework for a NMEA 0183 TCP Server inspired by Flask developer API',
    url='https://github.com/robonation/nmeaserver',
    download_url = 'https://github.com/robonation/nmeaserver/archive/v0.1.tar.gz',
    author='Felix Pageau',
    author_email='pageau@robonation.org',
    license='Apache License 2.0',
    install_requires=['numpy'],
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    long_description_content_type="text/markdown",
    long_description=open('README.md').read(),
    keywords = ['NMEA', 'SERVER', 'FRAMEWORK'],
    classifiers=[
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: Apache Software License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
      ],
)