#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

__version__ = "2.0"

setup(name='kTBS',
      version = __version__,
      description='A kernel for trace-based systems',
      long_description='A kernel for trace-based systems',
      author='Pierre-Antoine Champin, Françoise Conil',
      author_email='sbt-dev@liris.cnrs.fr',
      license='LGPL v3',
      platforms='Linux, MacOsX',
      url='http://github.com/ktbs/ktbs',
      package_dir = {'': 'lib'},
      packages=['rdfrest', 
                'rdfrest.plugins', 
                'rdfrest.plugins.serializers', 
                'ktbs', 
                'ktbs.local', 
                'ktbs.common', 
                'ktbs.client', 
                'ktbs.methods', 
                'ktbs.plugins'],
      scripts=['bin/ktbs','bin/simple-collector']
     )
