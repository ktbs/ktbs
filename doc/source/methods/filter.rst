Filter
======

This method copies the obsels of the source trace if they pass the filter.

:sources: 1
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
  :after: the integer timestamp below which obsels are filtered out
  :before: the integer timestamp above which obsels are filtered out
  :afterDT: the datetime timestamp below which obsels are filtered out
  :beforeDT: the datetime timestamp above which obsels are filtered out
  :otypes: space-separated list of URIs indicating which obsel types must be
           kept in the computed trace
  :bgp: a SPARQL Basic Graph Pattern used to express additional criteria
        (see below)
:extensible: no

If parameter ``model`` (resp. ``origin``) is not provided,
the model (resp. origin) of the source trace will be used instead.

All filtering parameters are optional.
If not specified, they will not constrain the obsels at all.
For example, if ``otypes`` is not provided,
obsels will be kepts regardless of their type;
on the other hand, if ``otypes`` is provided,
only obsels with their type in the list will be kept.

Datetime timestamps can only be used
if the source origin is itself a datetime.
If a temporal boundary is given both as an integer and a datetime timestamp,
the datetime will be ignored.
Note that temporal boundaries are *inclusive*,
but obsels must be entirely contained in them.

The ``bgp`` parameter accepts any SPARQL BGP
(i.e. triple patterns, FILTER clauses)
used to add further criteria to the obsels to keep in the computed trace.
The SPARQL variables ``?obs``, ``?b`` and ``?e`` are bound respectively to
the obsel, its begin timestamp and its end timestamp.
The prefix ``m:`` is bound to the source trace model URI.
