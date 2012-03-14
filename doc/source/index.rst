.. KTBS documentation master file, created by
   sphinx-quickstart on Thu Jul 21 09:36:33 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

kTBS: a kernel for Trace-Based Systems
======================================

kTBS is a specific DBMS dedicated to traces.

This documentation first describes the `general concepts <concepts>`:doc: of trace-based systems, and how they are implemented in kTBS. It then describes the `RESTful API <rest>`:doc: exposed by kTBS. The last chapter is a `developer's documentation <devel>`:doc: for using kTBS directly from Python code, or for modifying it.

Contents:

.. toctree::
   :maxdepth: 2

   concepts
   tutorials
   rest
   devel

.. todo::

  add intersphinx links to ``webob`` and ``rdflib``

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. note:: This documentation is kept as reStructuredText documents, managed
          with Sphinx_. 

.. _Sphinx: http://sphinx.pocoo.org/
