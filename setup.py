#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

from os.path import dirname, join
from sys import argv
from warnings import filterwarnings

__version__ = "0.2"

readme_rst = join(dirname(argv[0]), "README.rst")
long_description = open(readme_rst).read()

requirements_txt = join(dirname(argv[0]), "requirements.txt")
install_req = [ i[:-1] for i in open(requirements_txt) if i[0] != "#" ]
requirements = [ "%s (==%s)" % tuple(i.split("==")) for i in install_req ]

filterwarnings('ignore', message=".*Unknown distribution option: 'install_requires'.*")

setup(name='kTBS',
      version = __version__,
      description='A kernel for trace-based systems',
      long_description=long_description,
      author='Pierre-Antoine Champin, Françoise Conil',
      author_email='sbt-dev@liris.cnrs.fr',
      license='LGPL v3',
      platforms='OS Independant',
      url='http://github.com/ktbs/ktbs',
      package_dir = {'': 'lib'},
      packages=['rdfrest', 
                'ktbs', 
                'ktbs.api', 
                'ktbs.engine', 
                'ktbs.methods', 
                'ktbs.plugins'],
      scripts=['bin/ktbs','bin/simple-collector'],
      data_files = ['README.rst', 'requirements.txt',],
      requires=requirements,
      install_requires=install_req,
     )
