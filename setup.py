#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
from setuptools import find_packages, setup, Command

CURDIR = os.path.abspath(os.path.dirname(__file__))

EXCLUDE_FROM_PACKAGES = []
REQUIRED = [
    "pygdbmi>=0.8.4.0, <0.9",
    "python-socketio>=2.0.0",
]

README = io.open(os.path.join(CURDIR, "README.md"), "r", encoding="utf-8").read()
VERSION = (
    io.open(os.path.join(CURDIR, "VERSION.txt"), "r", encoding="utf-8")
    .read()
    .strip()
)


class TestCommand(Command):
    description = "test task"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # import here so dependency error on Flask is not
        # raised
        from tests import test_app

        sys.exit(test_app.main())


setup(
    name="pygdbcli",
    version=VERSION,
    author="Willem van Ketwich",
    author_email="willvk@gmail.com",
    description="Cli frontend to gdb. Debug C, C++, Go, or Rust.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/wilvk/pygdbcli",
    license="License :: GNU GPLv3",
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    include_package_data=True,
    keywords=[
        "gdb",
        "debug",
        "c",
        "c++",
        "go",
        "rust",
        "python",
        "machine-interface",
        "browser",
        "gui",
    ],
    scripts=[],
    entry_points={
        "console_scripts": [
        ]
    },
    extras_require={},
    zip_safe=False,
    cmdclass={"test": TestCommand},
    install_requires=REQUIRED,
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
