Obsel
=====

Obsels (short for 'Observed elements') are the atomic elements of traces. An obsel is described by the following elements:

* an obsel type,
* a begin timestamp,
* an end timestamp (that can equal the begin timestamp),
* an optional subject (the agent being traced).

It can also have multiple attributes, and be linked to other obsels of the same trace through binary relations.

The obsel type, the attributes and the relations are described by a :doc:`trace model <trace_model>`.

.. _obsel_total_ordering:

Obsel total ordering
++++++++++++++++++++

When orders of a trace need to be ordered,
kTBS uses a total ordering considering

* their end timestamp, then
* their begin timestamp, then
* their identifier.

So obsels with different timestamps will be ordered according to their end timestamps;
obsels with the same end timestamp but different begin timestamps will be ordered according to the latter;
obsels with the exact same timestamps will be ordered according to their identifiers.
