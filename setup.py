#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from ast import literal_eval
import re

def get_version(source='lib/ktbs/__init__.py'):
    with open(source) as f:
        for line in f:
            if line.startswith('__version__'):
                return literal_eval(line.partition('=')[2].lstrip())
    raise ValueError("VERSION not found")

with open('README.rst', 'r') as f:
    README = f.read()

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
      install_requires=['rdflib==4.1.1', 
                        'httplib2==0.8',
                        'WebOb==1.3.1',
                        'PyLD==0.4.10'],
      scripts=['bin/ktbs','bin/simple-collector','bin/ktbs-infos'],

      # py2exe
      console = ['bin/ktbs',],
      options = {
          "py2exe": {
	      "packages": [ "rdflib.plugins", "ktbs.plugins", ],
	  },
      },
    )
