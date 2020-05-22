Obsel
=====

Creation
--------

An obsel is created by a POST query to a `StoredTrace`. It must have the following properties:

* http://liris.cnrs.fr/silex/2009/ktbs#hasTrace linking to the Trace

Optionally, it may have the following properties:

* ``rdf:type`` valued with one or several obsel type defined by the trace model
* http://liris.cnrs.fr/silex/2009/ktbs#hasBegin (see below)
* http://liris.cnrs.fr/silex/2009/ktbs#hasBeginDT (see below)
* http://liris.cnrs.fr/silex/2009/ktbs#hasEnd (see below)
* http://liris.cnrs.fr/silex/2009/ktbs#hasEndDT (see below)
* http://liris.cnrs.fr/silex/2009/ktbs#hasSubject identifying the person/agent being traced
* any attribute or relation defined by the trace model.

Specifying temporal bounds
``````````````````````````

If the trace's `origin <origin>`:ref: is opaque:

* ``hasBegin`` must be specified;
* ``hasBeginDT`` and ``hasEndDT`` must not used;
* if ``hasEnd`` is not specified,
  the obsel will be considered to end at the same timestamp as its begin.

Otherwise, the trace's `origin <origin>`:ref: is a timestamp:

* if neither ``hasBegin`` nor ``hasBeginDT`` is specified,
  the obsel will be considered to begin at the current time;
* if neither ``hasEnd`` nor ``hasEndDT`` is specified,
  the obsel will be considered to end at the same timestamp as its begin.

GET
---

Return the description of this obsel.

DELETE
------

Deletes this obsel from the trace.
Note that this is a `non-monotonic <../concepts/monotonicity>`:doc: change.

NB: any other modification to an obsel is made through an amendment (PUT)
of the whole `obsel collection <obsel_collection>`:ref:.
