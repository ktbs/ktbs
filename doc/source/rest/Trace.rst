Trace
=====

This class is the base class of `StoredTrace`:doc: and `ComputedTrace`:doc:. It has no direct instances (only the two subclasses above can be instantiated), but everything described here is valid for any indirect instance.

Traces have one :ref:`aspect resource <rest-aspect-resource>`:

* `@obsels`_, linked through http://liris.cnrs.fr/silex/2009/ktbs#hasObselCollection

Original resource
+++++++++++++++++

GET
---

Retrieve the description of the trace, augmented with the following generated properties:

* http://liris.cnrs.fr/silex/2009/ktbs#compliesWithModel can be either "yes", "no" or "?" (if the model is not available)
* links to the @obsel aspect resource.

PUT
---

This allows to change the description of the trace itself.

DELETE
------

Deletes the trace and its aspect resources.

TODO: what happens if the trace is the source of a computed trace?

Description Constraints
-----------------------

The description of a trace must be `star shaped <star-shaped>`:ref:.


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
