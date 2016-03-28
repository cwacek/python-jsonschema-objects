#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <python_jsonschema_objects - An object wrapper for JSON Schema definitions>
# Copyright (C) <2014-2016>  Chris Wacek <cwacek@gmail.com

import ast
import os
import re
import sys
from setuptools import setup, find_packages


import versioneer


def parse_requirements(path):
    """Rudimentary parser for the `requirements.txt` file

    We just want to separate regular packages from links to pass them to the
    `install_requires` and `dependency_links` params of the `setup()`
    function properly.
    """
    try:
        print(os.path.join(os.path.dirname(__file__), *path.splitlines()))
        requirements = map(str.strip, local_file(path).splitlines())
    except IOError:
        raise RuntimeError("Couldn't find the `requirements.txt' file :(")

    links = []
    pkgs = []
    for req in requirements:
        if not req:
            continue
        if 'http:' in req or 'https:' in req:
            links.append(req)
            name, version = re.findall("\#egg=([^\-]+)-(.+$)", req)[0]
            pkgs.append('{0}=={1}'.format(name, version))
        else:
            pkgs.append(req)

    return pkgs, links


local_file = lambda *f: \
    open(os.path.join(os.path.dirname(__file__), *f)).read()


install_requires, dependency_links = \
    parse_requirements('requirements.txt')

if __name__ == '__main__':
    if 'register' in sys.argv or 'upload' in sys.argv:
        import register
        try:
          long_description = register.markdown_to_rst("README.md")
          if len(long_description) < 1:
            raise Exception("Failed to convert README.md")
        except Exception as e:
          sys.stderr.write("Error: {0}\n".format(e))
          sys.exit(1)

    else:
        long_description = ''

    setup(name='python_jsonschema_objects',
          version=versioneer.get_version(),
          description='An object wrapper for JSON Schema definitions',
          author='Chris Wacek',
          long_description=long_description,
          license="MIT",
          author_email='cwacek@gmail.com',
          packages=find_packages(),
          include_package_data=True,
          package_data={'python_jsonschema_objects.examples': ["README.md"]},
          zip_safe=False,
          url='http://python-jsonschema-objects.readthedocs.org/',
          setup_requires=["setuptools>=18.0.0"],
          install_requires=install_requires,
          dependency_links=dependency_links,
          cmdclass=versioneer.get_cmdclass()
    )
