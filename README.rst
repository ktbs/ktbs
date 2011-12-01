===========
Python kTBS
===========

This project is actually made of two subprojects:

rdfrest:
  A framework for RDF-based REST-ful services
kTBS:
  A kernel for trace-based systems (python implementation)

.. WARNING::

  Only the client side API of kTBS is (partly) operational.

  For the server part, please still use the old SVN for the moment:

  https://svn.liris.cnrs.fr/sbt-dev/ktbs-rest-impl

Dependencies
============

* rdflib 3.x (*Warning:* the appropriate 3.x version may not be
  available as a standard package in some linux distributions, see
  below for instructions on how to install it in this case.)
* httplib2
* webob (server part only)
* nose (developers)
* pylint (developers)
* sphinx (for building the documentation)

If you are using `virtualenv`_, an easy way to get up and running is to run::

  virtualenv --no-site-packages ./env
  source env/bin/activate
  pip install rdflib httplib2 webob nose pylint sphinx

and check that everything is ok with::

  make unittests

.. _virtualenv: http://pypi.python.org/pypi/virtualenv

Licence
=======

GPL v3
