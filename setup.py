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

with open('requirements.txt', 'r') as f:
    req_parts = [
                r'(?P<pname>[a-zA-Z\-\_0-9\.]+)',
                r'(?P<poperator>[\<\>\=]*)',
                r'(?P<pversion>[0-9\.\-a-zA-Z]*)'
                ]
    req_RE = r'\s*'.join(req_parts)
    req_pattern = re.compile(req_RE)

    install_req = [ i[:-1] for i in f if i[0] != "#" ]
    requirements = []
    for r in install_req:
        req_elt = req_pattern.match(r)
        if req_elt is not None:
            d = req_elt.groupdict()
            # distutils syntax ? not working
            # if d.get('poperator') is not None:
            #     requirements.append("%s (%s%s)" % (d['pname'],
            #                                        d['poperator'],
            #                                        d['pversion']))
            requirements.append("%s" % d['pname'])

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
      install_requires=requirements,
      scripts=['bin/ktbs','bin/simple-collector','bin/ktbs-infos'],

      # py2exe
      console = ['bin/ktbs',],
      options = {
          "py2exe": {
	      "packages": [ "rdflib.plugins", "ktbs.plugins", ],
	  },
      },
    )
