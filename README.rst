===========
Python kTBS
===========

This project is actually made of two subprojects:

rdfrest:
  A framework for RDF-based REST-ful services
kTBS:
  A kernel for trace-based systems (python implementation)

.. WARNING::

  Only the client side API of kTBS is (partly) functionnal.

  For the server part, please still use the old SVN for the moment:

  https://svn.liris.cnrs.fr/sbt-dev/ktbs-rest-impl

Dependancies
============

* rdflib 3.x
* httplib2
* webob (server part only)
* nose (developers)
* pylint (developers)

If you are using `virtualenv`, an easy way to get up and running is to run::

  virtualenv --no-site-packages ./env
  source env/bin/activate
  pip install rdflib httplib2 webob nose pylint

and check that everyrthing is ok with::

  make unittests

.. _virtualenv: http://pypi.python.org/pypi/virtualenv

Licence
=======

GPL v3
