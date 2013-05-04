Model
=====

A model is a simple RDF graph defining the obsel types, attributes and relations according to the kTBS vocabulary.

Creation
--------

A model is created by a POST query to a `Base`. It must have the following properties:

* http://liris.cnrs.fr/silex/2009/ktbs#contains linking from the Base
* http://liris.cnrs.fr/silex/2009/ktbs#hasParentModel

It can optionally have the following properties:

* http://liris.cnrs.fr/silex/2009/ktbs#hasParameter 

GET
---

Return the conten of the graph.

PUT
---

Change the content of the model.

DELETE
------

Not implemented yet. TODO decide what to do if computed traces use this model.
