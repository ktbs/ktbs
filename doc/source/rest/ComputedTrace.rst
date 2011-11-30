Computed Trace
==============

A trace whose obsels are computed according to a `Method`:doc:, either from a number of *source* traces (transformed trace), or from external information (automatically collected trace). Although its obsel collection may be stored for performance issues, it can be assumed to be computed dynamically and always up-to-date w.r.t. the sources.

Original resource
+++++++++++++++++

Creation
--------

A computed trace is created by a POST query to a `Base`. It must have the following properties:

* http://liris.cnrs.fr/silex/2009/ktbs#contains linking from the Base
* http://liris.cnrs.fr/silex/2009/ktbs#hasMethod

It can optionally have the following properties:

* http://liris.cnrs.fr/silex/2009/ktbs#hasSource 
* http://liris.cnrs.fr/silex/2009/ktbs#hasParameter 


@obsels
+++++++

GET
---

In addition to the query-string parameters accepted by any trace, computed traces allow for the parameter ``quick`` to force the retrieval of the *current* state of the trace, even if its content is not up to date.
