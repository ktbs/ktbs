Incremental Sparql (ISparql)
============================

This method applies a SPARQL SELECT query to the source trace,
and builds new obsels with the result.

:sources: 1
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
  :sparql: a SPARQL SELECT query (required)
:extensible: yes (see below)

The SPARQL query must be a SELECT query.
Its WHERE clause must contain the magic string ``%(__subselect__)s``,
which will be replaced with a `subquery`_.
For each obsel of the source trace,
this subquery will yield its URI, begin timestamp and end timestamp as
``?sourceObsel``, ``?sourceBegin`` and ``?sourceEnd``.
You may then complement the WHERE clause as you see fit.

.. _subquery: https://www.w3.org/TR/sparql11-query/#subqueries

Each row returned by your SELECT query will create a new obsel in the computed trace;
each variable will add information to the obsel,
based on the name of the variable, as explained by the table below.
Note that variables followed with a star (*) are mandatory :

.. list-table::

   * - ``sourceObsel`` *
     - a source obsel (``ktbs:hasSourceObsel``),
       also used to mint the URI of the computed obsel
   * - ``type`` *
     - the obsel type (``rdf:type``)
   * - ``begin`` *
     - the begin timestamp (``ktbs:hasBegin``)
   * - ``end``
     - the end timestamp (``ktbs:hasEnd``),
       copied from ``begin`` if not provided
   * - ``beginDT``
     - the begin datetime (``ktbs:hasBeginDT``);
       note that kTBS does *not* check the consistency with ``begin``
   * - ``endDT``
     - the end datetime (``ktbs:hasEndDT``),
       note that kTBS does *not* check the consistency with ``end``
   * - ``subject``
     - the subject of the obsel (``ktbs:hasSubject``)
   * - (any name starting with ``sourceObsel``)
     - an additional source obsel (``ktbs:hasSourceObsel``)
   * - (any other name)
     - an attribute built by concatenating the variable name
       to the namespace of the computed trace's model

If parameter ``model`` (resp. ``origin``) is not provided,
the model (resp. origin) of the source trace will be used instead.

The SPARQL query can contain magic strings of the form ``%(param_name)s``,
that will be replaced by the value of
an additional parameter named ``param_name``.

.. _isparql_limitation:

.. important::

   For the sake of performance, this method works *incrementally*:
   everytime the trace is re-computed,
   the `subquery`_ inserted at ``%(__subselect__)s``
   magically selects only source obsels that have not been considered yet.

   As a consequence,
   each results of the query should **not depend**
   on information that appears "later" in the trace than ``?sourceObsel``.
   Otherwise, the content of the computed trace may vary unpredictably,
   depending on when the trace is actually computed.

   If you can not guarantee the property above,
   then you should probably use the `sparql <sparql>`:doc: method below instead,
   understanding that it will not behave as well performancewise.
