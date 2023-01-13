#!/usr/bin/env python
from setuptools import setup, find_packages

wds_version = "0.1.103"

install_requires = [f"webdataset=={wds_version}"]

setup(
    name="smd_simple",
    version="0.1",
    author="jbsnyder",
    url="https://github.com/johnbensnyder/smd_simple",
    description="simple smd resnet model",
    packages=find_packages(),
    install_requires=install_requires,
)