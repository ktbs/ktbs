#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import join
from setuptools import setup, find_packages

from ast import literal_eval
import re

def get_version(source='lib/ktbs/__init__.py'):
    with open(source) as f:
        for line in f:
            if line.startswith('__version__'):
                return literal_eval(line.partition('=')[2].lstrip())
    raise ValueError("VERSION not found")

README = ''
with open('README.rst', 'r') as f:
    README = f.read()

install_req = []
with open(join('requirements.d', 'base.txt'), 'r') as f:
    # Get requirements depencies as written in the file
    install_req = [ i[:-1] for i in f if i[0] != "#" ]

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
      install_requires=install_req,
      scripts=['bin/ktbs',
               'bin/ktbs-infos',
               'bin/ktbs-rebase', 
               'bin/ktbs-reset-locks', 
               'bin/simple-collector',
           ],

      # py2exe
      console = ['bin/ktbs',],
      options = {
          "py2exe": {
	      "packages": [ "rdflib.plugins", "ktbs.plugins", ],
	  },
      },
    )
