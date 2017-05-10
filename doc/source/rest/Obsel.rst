Obsel
=====

Creation
--------

An obsel is created by a POST query to a `StoredTrace`. It must have the following properties:

* http://liris.cnrs.fr/silex/2009/ktbs#hasTrace linking to the Base
* http://liris.cnrs.fr/silex/2009/ktbs#hasBegin (see below)
* http://liris.cnrs.fr/silex/2009/ktbs#hasEnd (see below)

It can also have any attribute or relation defined by the trace model.

GET
---

Return the description of this obsel.

DELETE
------

Deletes this obsel from the trace.
Note that this is a `non-monotonic <monotonicity>`:doc: change.

NB: any other modification to an obsel is made through an amendment (PUT)
of the whole `obsel collection <obsel_collection>`:ref:.
