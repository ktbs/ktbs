Stored Trace
=============

A trace whose obsels are created externally by POSTing them to the trace, and stored by the system. In addition to the interface specified by its superclass `Trace`:doc:, this class accepts the following requests.

Original resource
+++++++++++++++++

Creation
--------

A stored trace is created by a POST query to a `Base`. It must have the following properties:

* http://liris.cnrs.fr/silex/2009/ktbs#contains linking from the Base
* http://liris.cnrs.fr/silex/2009/ktbs#hasModel
* http://liris.cnrs.fr/silex/2009/ktbs#hasOrigin 

POST
----

Add an `obsel <Obsel>`:doc: to that trace. See the section about :doc:`../concepts/monotonicity` for a discussion the constraints.


@obsels
+++++++

PUT
---

This allows to amend the content of the trace.

Note that this allows to modify obsels, although they appear to be child resources of the trace. This is an exception to the `rule <child-modification>`:ref: stating that a resource can not be modified by altering its parent resource.
