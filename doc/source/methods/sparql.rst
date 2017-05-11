Sparql
======

.. important::

  Unlike other methods,
  this method does not work incrementally: each time the source trace is modified,
  the whole computed trace is re-generated.

  Therefore,
  you should consider using the
  `incremental sparql <isparql>`:doc: method instead,
  unless `its limitations <isparql_limitation>`:ref:
  are too constraining for your needs.

This method applies a SPARQL CONSTRUCT query to the source trace.

:sources: 1
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
  :sparql: a SPARQL CONSTRUCT query (required)
  :scope: graph against which the SPARQL query must be executed (see below)
  :inherit: inherit properties from source obsel (see below)
:extensible: yes (see below)

If parameter ``model`` (resp. ``origin``) is not provided,
the model (resp. origin) of the source trace will be used instead.

The ``scope`` parameter accepts two values:
``trace`` (the default) and ``base``.
When scoped to the trace,
the SPARQL query only has access to the obsels of the source trace.
When scoped to the base,
the SPARQL query has access to the information of the whole base.
This can be useful to use external information that the obsels of the source trace link to,
such as model information
(if the model is stored in the same base as the source trace),
source obsels
(if the source trace is itself a computed trace),
etc.
Also, when scoped to the base,
the SPARQL query can use the ``GRAPH`` keyword to constrain or retrieve the provenance of triples.

If ``inherit`` is set (with any value),
then the produced obsels will inherit from their source obsel
all the properties that are not explicitly set by the CONSTRUCT.
That includes properties in the ``ktbs`` namespace.
This allows to greatly simplify SPARQL queries that are mostly
filtering and or augmenting obsels, rather than synthetizing new ones.
Note however that if the obsel has several source obsels,
the behabiour is unspecified.
Note also that this mechanism can access the source obsels regardless of the ``scope``.

The SPARQL query can contain magic strings of the form ``%(param_name)s``,
that will be replaced by the value of
an additional parameter named ``param_name``.
Note that the following special parameters are automatically provided:

======================== ======================================================
 special parameter name   replaced by
======================== ======================================================
 ``__destination__``      The URI of the computed trace.
 ``__source__``           The URI of the source trace.
======================== ======================================================
