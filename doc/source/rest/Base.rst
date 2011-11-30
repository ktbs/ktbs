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

PUT
---

Not implemented yet. Eventually, this will allow to change some information about the base. Items of a base can not be modified that way, and may therefore be ommitted from the payload.

DELETE
------

Not implemented yet. Deletes the base.

TODO: decide whether a base can be deleted if it is not empty.

Description constraints
-----------------------

The descrtiption of a base must be `star shaped <star-shaped>`:ref:.

