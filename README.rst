===========
Python kTBS
===========

This project is actually made of two subprojects:

rdfrest:
  A framework for RDF-based REST-ful services
kTBS:
  A kernel for trace-based systems (python implementation)


Dependencies
============

* rdflib 4 (*Warning:* the appropriate version may not be
  available as a standard package in some linux distributions, see
  below for instructions on how to install it in this case.)
* httplib2
* webob
* pyld (for JSON support)

See ``requirements.txt`` for the required versions. 

For developpers
---------------

* nose (for testing)
* pylint (for checking code quality)

See ``requirements-dev.txt``.

To build the documentation locally
----------------------------------

* sphinx (for building the documentation)

Install
=======

See the tutorial_.

.. _tutorial: https://kernel-for-trace-based-systems.readthedocs.org/en/latest/tutorials/install.html

Tests
=====

.. image:: https://travis-ci.org/ktbs/ktbs.png?branch=develop
        :target: https://travis-ci.org/ktbs/ktbs

Licence
=======

LGPL v3
