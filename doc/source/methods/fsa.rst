Finite State Automaton (FSA)
============================

This method applies a Finite State Automaton to detect patterns of obsels in the source trace,
and produce an obsel in the transformed trace for each pattern occurence.
It is based on the FSA4streams_ library.

.. _FSA4streams: https://pypi.python.org/pypi/fsa4streams

:sources: 1
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
  :fsa: the description of the FSA
:extensible: no

If parameter ``model`` (resp. ``origin``) is not provided,
the model (resp. origin) of the source trace will be used instead.

The ``fsa`` parameter expects a JSON description of the FSA,
as described in the `FSA4streams documentation <http://fsa4streams.readthedocs.org/en/latest/syntax.html>`_,
with the following specificities:

* The default matcher (even if not explicitly specified) is ``obseltype``:
  each ``transition.condition`` is interpreted as an obsel type URI
  (either absolute or relative to the source trace's model URI),
  and an obsel matches the transition if it has the corresponding obsel type.

* An additional matcher is also provided: ``sparql-ask``,
  which allows for more expressive condition as the previous one.
  It interprets conditions as the WHERE clause of a SPARQL ASK query,
  where

  - prefix ``:`` is bound to the kTBS namespace,
  - prefix ``m:`` is bound to the source trace model,
  - variable ``?obs`` is bound to the considered obsel,
  - variable ``?pred`` is bound to the previous matching obsel (if any),
  - variable ``?first`` is bound to the first matching obsel of the current match (if any).

* The ``max_duration`` constraints (as specified in the documentation)
  apply to the *end* timestamps of the obsels.

* Terminal states may have two additional attributes ``ktbs_obsel_type`` and ``ktbs_attribute``,
  described below.

For each match found by the FSA,
a new obsel is generated:

* The source obsels of the new obsel are all the obsels contributing to the match.

* The begin and end timestamps of the new obsel are, respectively,
  the begin of the first source obsel and the end of the last source obsel.

* The type of the new obsel is the value of the ``ktbs_obsel_type`` of the terminal state,
  interpreted as a URI relative to the computed trace's model URI.
  If this attribute is omitted, the state identifier is used instead.

* If the terminal state has a ``ktbs_attributes`` model,
  additional attributes will be generated for the new obsel.
  The value of ``ktbs_attributes`` must be a JSON object,
  whose keys are the *target* attribute type URIs
  (relative to the computed trace's model URI),
  and whose values are *source* attribute type URIs
  (relative to the source trace's model URI).
  Each target attribute will receive the value of the source attribute of the source obsels.
  If several values are available, the value of the latest source obsel will be kept.
  If none of the source obsel has a source attribute,
  the corresponding target attribute will not be set.

  Additionally,
  the source attributes can be preceded by one of the following operators,
  in which case the value of the target operator will be the result of applying the operator to all the values of the source attributes in the source obsels:

  * ``last``: returns the last value in chronological order (this is the default, see above);
  * ``first``: returns the first value in chronological order;
  * ``count``: returns the number of source obsel having the source attribute;
  * ``sum``: returns the sum of all values;
  * ``avg``: returns the average of all values;
  * ``min``: returns the minimum value;
  * ``max``: returns the maximum value;
  * ``span``: returns the difference between the maximum and the minimum values;
  * ``concat``: returns a space-separated concatenation of all the values.
