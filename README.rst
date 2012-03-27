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

If you are using `virtualenv`_, an easy way to get up and running is to run:

.. code-block:: bash

    $ virtualenv --no-site-packages ktbsenv
    $ cd ktbsenv
    $ source bin/activate
    $ git clone git://github.com/ktbs/ktbs.git
    $ cd ktbs/
    $ pip install -r requirements.txt
    $ python setup.py install

.. note::

    If you want to run the test suite, you must uncomment the "developper's part" in requirements.txt

To run the test suite:

.. code-block:: bash

    $ make unit-tests

.. _virtualenv: http://pypi.python.org/pypi/virtualenv 


Licence
=======

LGPL v3
