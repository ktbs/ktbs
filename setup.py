#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from ast import literal_eval

def get_version(source='lib/__init__.py'):
    with open(source) as f:
        for line in f:
            if line.startswith('__version__'):
                return literal_eval(line.partition('=')[2].lstrip())
    raise ValueError("VERSION not found")

with open('README.rst', 'r') as f:
    README = f.read()

with open('requirements.txt', 'r') as f:
    install_req = [ i[:-1] for i in f if i[0] != "#" ]
    # Not robust if we use something different from '==' for requirements
    requirements = [ "%s (==%s)" % tuple(i.split("==")) for i in install_req ]

setup(name = 'kTBS',
      version = get_version(),
      package_dir = {'': 'lib'},
      packages = find_packages(where='lib'),
      description = 'A kernel for trace-based systems',
      long_description = README,
      author='Pierre-Antoine Champin, Françoise Conil',
      author_email='sbt-dev@liris.cnrs.fr',
      license='LGPL v3',
      platforms='OS Independant',
      url='http://github.com/ktbs/ktbs',
      include_package_data=True,
      requires=requirements,
      install_requires=install_req,
      scripts=['bin/ktbs','bin/simple-collector'],

      # py2exe
      console = ['bin/ktbs',],
      options = {
          "py2exe": {
	      "packages": [ "rdflib.plugins", "ktbs.plugins", ],
	  },
      },
    )
