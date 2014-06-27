#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <python_jsonschema_objects - An object wrapper for JSON Schema definitions>
# Copyright (C) <2014-2014>  Chris Wacek <cwacek@gmail.com
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see <http://www.gnu.org/licenses/>

import ast
import os
import re
import sys
from setuptools import setup, find_packages


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
          version='0.0.10',
          description='An object wrapper for JSON Schema definitions',
          author='Chris Wacek',
          long_description=long_description,
          author_email='cwacek@gmail.com',
          include_package_data=True,
          url='http://github.com/cwacek/python-jsonschema-objects',
          packages=find_packages(exclude=['*tests*']),
          install_requires=install_requires,
          dependency_links=dependency_links,
    )
