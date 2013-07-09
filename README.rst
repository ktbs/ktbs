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

* rdflib 3.x (*Warning:* the appropriate 3.x version may not be
  available as a standard package in some linux distributions, see
  below for instructions on how to install it in this case.)
* rdfextras
* httplib2
* webob (>=1.2, server part only)

To build the documentation
--------------------------
* sphinx (for building the documentation)

For developpers
---------------
* pyld (for the jsonld plugin -- https://github.com/digitalbazaar/pyld/tree/master/lib )
* nose (developers)
* pylint (developers)

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
