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

NB: any modification to an obsel is made through an amendment (PUT) of the trace.
