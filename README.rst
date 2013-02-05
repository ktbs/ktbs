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

If you are using `virtualenv`_, an easy way to get up and running is to run::

    $ virtualenv --no-site-packages ktbsenv
    $ cd ktbsenv
    $ source bin/activate
    $ pip install -r requirements.txt
    $ git clone git://github.com/ktbs/ktbs.git
    $ cd ktbs/
    $ python setup.py install

Note::

    If you want to run the test suite, you must uncomment the "developper's part" in requirements.txt

To run the test suite::

    $ make unit-tests

.. _virtualenv: http://pypi.python.org/pypi/virtualenv 


Licence
=======

LGPL v3
