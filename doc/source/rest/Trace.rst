Trace
=====

This class is the base class of `StoredTrace`:doc: and `ComputedTrace`:doc:. It has no direct instances (only the two subclasses above can be instantiated), but everything described here is valid for any indirect instance.

Traces have two :ref:`aspect resources <rest-aspect-resource>`:

* `@about`_, linked through http://liris.cnrs.fr/silex/2009/ktbs#descriptionOf
* `@obsels`_, linked through http://liris.cnrs.fr/silex/2009/ktbs#hasObselCollection

Original resource
+++++++++++++++++

GET
---

Redirects (with a 303 HTTP status) to the `@about`_ aspect resource.

DELETE
------

Not implemented yet. Deletes the trace and its aspect resources.

TODO: what happens if the trace is the source of a computed trace?


@about
++++++

This aspect resource stands for the metadata about the trace.

GET
---

Retrieve the decription of the trace, augemnted with the following generated properties:

* http://liris.cnrs.fr/silex/2009/ktbs#compliesWithModel can be either "yes", "no" or "?" (if the model is not available)
* links to the @about and @obsel aspect resources.

PUT
---

This allows to change the description of the trace itself.

Description Constraints
-----------------------

The descrtiption of a trace must be `star shaped <star-shaped>`:ref:.


@obsels
+++++++

This aspect resource stands for the obsel collection of the trace.

GET
---

Return the description of all the obsels of the trace. This description can be filtered by passing the following query-string arguments:

:minb: minimum begin
:mine: minimum end
:maxb: maximum begin
:maxe: maximum end
:id: will only describe the obsel(s) with the given identifier(s) 

For example http://localhost:8001/base1/t01/@obsels?minb=42&maxe101 will return only those obsel beginning at or after 42 and ending at or before 101.
