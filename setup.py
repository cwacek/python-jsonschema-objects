#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <python_jsonschema_objects - An object wrapper for JSON Schema definitions>
# Copyright (C) <2014-2016>  Chris Wacek <cwacek@gmail.com

import sys

from setuptools import find_packages, setup

import versioneer

if __name__ == "__main__":
    if "register" in sys.argv or "upload" in sys.argv:
        import register

        try:
            long_description = register.markdown_to_rst("README.md")
            if len(long_description) < 1:
                raise Exception("Failed to convert README.md")
        except Exception as e:
            sys.stderr.write("Error: {0}\n".format(e))
            sys.exit(1)

    else:
        long_description = ""

    setup(
        name="python_jsonschema_objects",
        version=versioneer.get_version(),
        description="An object wrapper for JSON Schema definitions",
        author="Chris Wacek",
        long_description=long_description,
        license="MIT",
        author_email="cwacek@gmail.com",
        packages=find_packages(),
        include_package_data=True,
        package_data={"python_jsonschema_objects.examples": ["README.md"]},
        zip_safe=False,
        url="http://python-jsonschema-objects.readthedocs.org/",
        setup_requires=["setuptools>=18.0.0"],
        install_requires=[
            "inflection>=0.2",
            "Markdown>=2.4",
            "jsonschema>=4.18",
        ],
        python_requires=">=3.8",
        cmdclass=versioneer.get_cmdclass(),
        classifiers=[
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Intended Audience :: Developers",
            "Development Status :: 4 - Beta",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
    )
