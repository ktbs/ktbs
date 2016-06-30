Base
====

Base resources represent the trace bases hosted by the system.

Creation
--------

A base is created by a POST query to the `KtbsRoot`. It must have the following properties:

* http://liris.cnrs.fr/silex/2009/ktbs#hasBase linking from the KtbsRoot
 

GET
---

Retrieve a description of the base. This description contains information about the base (label, owner, etc.) and the list of items (`Trace`:doc:, `Model`:doc:, `Method`:doc:) it contains, with their types.

It is also possible to enrich the graph returned by GET with information about the items of the base,
using the property ``prop`` containing a comma-separated list of the following properties:

* ``comment`` to display the ``rdfs:comment``\ s of items,
* ``hasModel`` to display the model of traces,
* ``hasSource`` to display the sources of traces,
* ``label`` to display the ``rdfs:label``\ s of ``skos:prefLabel`` of items,
* ``obselCount`` to display the number of obsels of traces.

PUT
---

This allows to change some information about the base. Items of a base can not be modified that way, and may therefore be ommitted from the payload.

DELETE
------

Deletes the base.

TODO: decide whether a base can be deleted if it is not empty.

Description constraints
-----------------------

The description of a base must be `star shaped <star-shaped>`:ref:.

