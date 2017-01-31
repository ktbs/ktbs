Method
======

A method is used by a computed trace to determine its model and origin, and to generate its obsels. The kTBS a number of built-in methods, described below. It is also possible to create user-defined methods, that are stored in a base besides trace models and traces.

Built-in methods
----------------

Filter
``````

This method copies the obsels of the source trace if they pass the filter.

:sources: 1
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
  :after: the integer timestamp below which obsels are filtered out 
  :before: the integer timestamp above which obsels are filtered out 
  :afterDT: the datetime timestamp below which obsels are filtered out 
  :beforeDT: the datetime timestamp above which obsels are filtered out 
  :otypes: space-separated list of URIs indicating which obsel types must be
           kept in the computed trace
  :bgp: a SPARQL Basic Graph Pattern used to express additional criteria
        (see below)
:extensible: no

If parameter ``model`` (resp. ``origin``) is not provided,
the model (resp. origin) of the source trace will be used instead.

All filtering parameters are optional.
If not specified, they will not constrain the obsels at all.
For example, if ``otypes`` is not provided,
obsels will be kepts regardless of their type;
on the other hand, if ``otypes`` is provided,
only obsels with their type in the list will be kept.

Datetime timestamps can only be used
if the source origin is itself a datetime.
If a temporal boundary is given both as an integer and a datetime timestamp,
the datetime will be ignored.
Note that temporal boundaries are *inclusive*,
but obsels must be entirely contained in them.

The ``bgp`` parameter accepts any SPARQL BGP
(i.e. triple patterns, FILTER clauses)
used to add further criteria to the obsels to keep in the computed trace.
The SPARQL variables ``?obs``, ``?b`` and ``?e`` are bound respectively to
the obsel, its begin timestamp and its end timestamp.
The prefix ``m:`` is bound to the source trace model URI.


Fusion
``````

This method merges the content of all its sources.

:sources: any number
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
:extensible: no

If all source traces have the same model (resp. origin),
then parameter ``model`` (resp. ``origin``) is not required,
and in that case the computed trace will have
the same model (resp. origin) as its source(s).


FSA
```

This method applies a Finite State Automaton to detect patterns of obsels in the source trace,
and produce an obsel in the transformed trace for each pattern occurence.
It is based on the FSA4streams_ library.

.. _FSA4streams: https://pypi.python.org/pypi/fsa4streams

:sources: 1
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
  :fsa: the description of the FSA
:extensible: no

If parameter ``model`` (resp. ``origin``) is not provided,
the model (resp. origin) of the source trace will be used instead.

The ``fsa`` parameter expects a JSON description of the FSA,
as described in the `FSA4streams documentation <http://fsa4streams.readthedocs.org/en/latest/syntax.html>`_,
with the following specificities:

* The default matcher (even if not explicitly specified) is ``obseltype``:
  each ``transition.condition`` is interpreted as an obsel type URI
  (either absolute or relative to the source trace's model URI),
  and an obsel matches the transition if it has the corresponding obsel type.

* An additional matcher is also provided: ``sparql-ask``.
  It interprets conditions as the WHERE clause of a SPARQL ASK query,
  where prefix ``:`` and ``m:`` are bound to the kTBS namespace and the source trace model,
  respectively,
  variable ``?obs`` is bound to the considered obsel,
  and a variable ``?pred`` is bound to the previous matching obsel (if any).
  This matcher allows for more expressive conditions.

* The ``max_duration`` constraints (as specified in the documentation)
  apply to the *end* timestamps of the obsels.

* Terminal states may have two additional attributes ``ktbs_obsel_type`` and ``ktbs_attribute``,
  described below.

For each match found by the FSA,
a new obsel is generated:

* The source obsels of the new obsel are all the obsels contributing to the match.

* The begin and end timestamps of the new obsel are, respectively,
  the begin of the first source obsel and the end of the last source obsel.

* The type of the new obsel is the value of the ``ktbs_obsel_type`` of the terminal state,
  interpreted as a URI relative to the computed trace's model URI.
  If this attribute is omitted, the state identifier is used instead.

* If the terminal state has a ``ktbs_attributes`` model,
  additional attributes will be generated for the new obsel.
  The value of ``ktbs_attributes`` must be a JSON object,
  whose keys are the *target* attribute type URIs
  (relative to the computed trace's model URI),
  and whose values are *source* attribute type URIs
  (relative to the source trace's model URI).
  Each target attribute will receive the value of the source attribute of the source obsels.
  If several values are available, the value of the latest source obsel will be kept.
  If none of the source obsel has a source attribute,
  the corresponding target attribute will not be set.

  Additionally,
  the source attributes can be preceded by one of the following operators,
  in which case the value of the target operator will be the result of applying the operator to all the values of the source attributes in the source obsels:

  * ``last``: returns the last value in chronological order (this is the default, see above);
  * ``first``: returns the first value in chronological order;
  * ``count``: returns the number of source obsel having the source attribute;
  * ``sum``: returns the sum of all values;
  * ``avg``: returns the average of all values;
  * ``min``: returns the minimum value;
  * ``max``: returns the maximum value;
  * ``span``: returns the difference between the maximum and the minimum values;
  * ``concat``: returns a space-separated concatenation of all the values.



Incremental Sparql (ISparql)
````````````````````````````
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
     - a source obsel (``ktbs:sourceObsel``),
       also used to mint the URI of the computed obsel
   * - ``type`` *
     - the obsel type (``rdf:type``)
   * - ``begin`` *
     - the begin timestamp (``ktbs:begin``)
   * - ``end``
     - the end timestamp (``ktbs:begin``),
       copied from ``begin`` if not provided
   * - ``beginDT``
     - the begin datetime (``ktbs:begin``);
       note that kTBS does *not* check the consistency with ``begin``
   * - ``endDT``
     - the end datetime (``ktbs:begin``),
       note that kTBS does *not* check the consistency with ``end``
   * - ``subject``
     - the subject of the obsel
   * - (any name starting with ``sourceObsel``)
     - an additional source obsel (``ktbs:sourceObsel``)
   * - (any other name)
     - an attribute built by concatenating the variable name
       to the namespace of the computed trace's model

If parameter ``model`` (resp. ``origin``) is not provided,
the model (resp. origin) of the source trace will be used instead.

The SPARQL query can contain magic strings of the form ``%(param_name)s``,
that will be replaced by the value of
an additional parameter named ``param_name``.

Sparql
``````

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

Note also that, unlike other methods, this method does not work incrementally: each time the source trace is modified, the whole computed trace is re-generated. This may be optimized in the future.


External
````````

This method invokes an external program to compute a computed trace.
The external program is given as a command line,
expected to produce the obsels graph of the computed trace.

:sources: any number
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
  :command-line: the command line to execute (required)
  :format: the format expected and produced by the command line
  :min-sources: the minimum number of sources expected by the command-line
  :max-sources: the maximum number of sources expected by the command-line
  :feed-to-stdin: whether to use the external command standard input
                  (see below)
       
:extensible: yes (see below)

If parameter ``model`` (resp. ``origin``) is not provided,
the model (resp. origin) of the source trace will be used instead.

The command line query can contain magic strings
of the form ``%(param_name)s``,
that will be replaced by the value of
an additional parameter named ``param_name``.
Note that the following special parameters are automatically provided:

======================== ======================================================
 special parameter name   replaced by
======================== ======================================================
 ``__destination__``      The URI of the computed trace.
 ``__sources__``          The space-separated list of the source traces' URIs.
======================== ======================================================

Parameter ``format`` is used to inform the kTBS
of the format produced by the command line. Default is ``turtle``.

Parameters ``min-sources`` and ``max-sources`` are used to inform the kTBS
of the minimum (resp. maximum) number of sources traces
expected by the command line.
This is especially useful in user-defined methods,
to control that the computed traces using them
are consistent with their expectations.

In the general case, the command line is expected to receive
the source trace(s) URI(s) as arguments,
and query the kTBS to retrieve their obsels.
As an alternative, parameter ``feed-to-stdin`` can be set
to have the kTBS send the source trace obsels
directly to the standard input of the external command process.
Note that this is only possible when there is exactly one source,
and the format used to serialize the obsels
will be the same as parameter ``format``.

Note also that, unlike other methods, this method does not work incrementally: each time the source trace is modified, the whole computed trace is re-generated. This may be optimized in the future.




User-defined methods
--------------------

A user defined method is described by:

* an inherited method (either built-in or user-defined),
* a number of parameters.

For simple methods such as filter, this is merely a way to define a reusable set of parameters. However, for more generic method such as Sparql or External, it provides a mean to encapsulate a complex transformation, possibly requiring its own parameters (via extensibility). 
