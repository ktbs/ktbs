Method
======

A method is used by a computed trace to determine its model and origin, and to generate its obsels. The kTBS a number of built-in methods, described below. It is also possible to create user-defined methods, that are stored in a base besides trace models and traces.

Built-in methods
----------------

Filter
++++++

This method copies the obsels of the source trace if they pass the filter. The model and origin of the trace are the same as the source.

For temporal filters, note boundaries are inclusive, but obsels must be entirely contained in them.

:sources: 1
:parameters:
  :start: the integer timestamp below which obsels are filtered out 
  :finish: the integer timestamp above which obsels are filtered out 
:extensible: no

Fusion
++++++

This method merges the content of all its sources.

The model of the fusionned trace can be provided as a parameter; if omitted, it will be expected that all sources have the same model, and that model will be the one of the fusionned trace.

Likewise, if all sources have the same origin, this origin will be the one of the fusionned trace; else, an opaque origin will be created.

:sources: any number
:parameters:
  :model: the URI of the model of the fusionned trace
:extensible: no

Note that this transformation guarantees the temporal :doc:`monotonicity` of the computed trace. This implies that obsels will appear in the computed trace with a delay. In the future, a parameter may be available to disable this behaviour.

Sparql rule
+++++++++++

This method applies a SPARQL CONSTRUCT query to the source trace. TODO model and origin

:sources: 1
:parameters:
  :sparql: a SPARQL CONSTRUCT query
  :model: the model URI of the computed trace (optional, see below)
  :origin: the origin of the computed trace (optional, see below)
:extensible: yes

If the parameter ``model`` (resp. ``origin``) is omitted, the model (resp. the origin) of the source trace is used.

The sparql query may contain parameters of the form ``%(param_name)s`` that will be replaced by the corresponding parameter value. 

Note also that, unlike other methods, this method does not work incrementally: each time the source trace is modified, the whole computed trace is re-generated. This may be optimized in the future.

Script/Python
+++++++++++++

This method allows to override the code of the method with Python function provided in its parameters.

:sources: 1
:parameters:
  :script: python functions
:extensible: yes (additional parameters defined by the script)

Super-method
++++++++++++

In many cases, one wants to apply several simple transformations to a single source trace, and fusion the result into a single transformed trace, without being interested in the several intermediate traces. The super-method lets the kTBS automatically manage those intermediate sources traces.

Note that intermediate traces are not completely hidden: they appear in the metadata of the transformed trace (as ``ktbs:hasIntermediateSource``), and the computed obsels may have their source obsel located in the intermediate traces. This allows to trace back which one of the sub-transformation produced which obsel.

:sources: 1
:parameters:
  :submethods: space-separated list of method URIs (relative to the *base*)
  :model: the model URI of the computed trace (optional, see below)
  :origin: the origin of the computed trace (optional, see below)
  :(other): any parameter accepted by `Fusion`_ is also accepted
:extensible: no

If the parameter ``model`` (resp. ``origin``) is omitted, the model (resp. the origin) of the source trace is used.


User-defined methods
--------------------

A user defined method is described by:

* an inherited method (either built-in or user-defined),
* a number of parameters.

For simple methods such as filter, this is merely a way to define a reusable set of parameters. However, for more generic method such as SPARQL or Script/Python, it provides a mean to encapsulate a complex transformation, possibly requiring its own parameters (for extensible methods). 
