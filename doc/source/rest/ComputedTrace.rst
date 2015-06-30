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

In addition to the query-string parameters accepted by any trace,
computed traces allow for the parameter ``refresh``
to control the computation process.
Recognized values are:

* ``default`` (which is the default value!)
    will refresh the trace only if needed
    (i.e. if its method, its parameters or its sources have changed).
* ``no`` will prevent any re-computation.
* ``yes`` or ``force`` will force the re-computation of the trace,
  even if nothing has changed.
* ``recursive`` will recursively force the re-computation of all the sources of the trace,
  then of the trace itself.
