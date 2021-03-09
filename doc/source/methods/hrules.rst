Hubble Rules (HRules)
=====================

This method is named after the Hubble_ project,
in which they have been proposed.
Those rules can be used both as a stylesheet in the `Taaabs timeline`_ component,
and as a transformation, thanks to this method.
A benefit is that such a transformation can be built interactively in the timeline,
with a direct visual feedback of its effect,
then "materialized" as a user-defined method and applied to other traces.

.. _Hubble: http://hubblelearn.imag.fr/
.. _Taaabs timeline: https://github.com/TaaabsElements/taaabs-trace-timeline

:sources: 1
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
  :rules: the description of the rules
:extensible: no

If parameter ``origin`` is not provided,
the origin of the source trace will be used instead.

The parameter `model` specified the model of the computed trace.
It must be specified
(as traces computed from rules generally hava a different model from their source trace).

The parameter `rules` is a JSON string complying with the model below.

Structure of the ``rules`` parameter
------------------------------------

The ``rule`` parameter contains a JSON array.
Each item of this array is called a *rule*.

Each *rule* is a JSON object with the following attributes:

- ``id`` is an obsel type IRI (from the target model),
  no two rules must have the same ``id``.
- ``rules`` is an array of *subrules*.
- ``visible`` is an optional boolean, defaulting to ``true``.

Each *subrule* is a JSON object with the following attributes:

- ``type`` is an optional obsel type IRI (from the source trace's model).
- ``attribute`` is an optional JSON array of *attribute constraints*.

Each *attribute constraint* is a JSON object with the following attributes:

- ``uri`` is an attribute type IRI (from the source trace's model).
- ``operator`` is one of the following strings: ``==``, ``!=``,
  ``<``, ``>``, ``<=``, ``>=``.
- ``value`` is either a JSON string or a `JSON-LD value object`_.

.. _JSON-LD value object: http://json-ld.org/spec/latest/json-ld/#value-objects

Semantics of Hubble rules
-------------------------

+ An obsel (from the source trace)
  matches an attribute constraint if it has the corresponding attribute,
  and its value satisfies the corresponding operator and value.

  If the ``value`` of the attribute constraint is a string,
  and if the attribute has a single datatype as its range in the source model,
  then the value will be cast to that datatype before the comparison is computed.
  Otherwise, it will be converted to a literal as specified by JSON-LD.

+ An obsel matches a subrule with a ``type`` if
  it matches *all* the attribute constraints of the subrule.

+ An obsel matches a subrule with a ``type`` if

  - it has the corresponding obsel type, and
  - it matches *all* the attribute constraints of the subrule.

+ An obsel matches a rule if it matches at least one of its subrule.

This method produces a new obsel for each source obsel matching a rule
(unless this rule has ``visible`` set to false);
the obsel type of the new obsel is the ``id`` of the matching rule;
the attributes of the source obsel are copied in the new obsel.

Precedence of subrules
----------------------

Whenever an obsel matches several subrules
(belonging to different rules),
the following precedence applies:

* a subrule which specifies an obsel type has precedence over a subrule which does not,
  regardless of their number of attribute constraints or position in the rule structure;

* a subrules with more attribute constraings has precedence over a subrule with less attributes constraints,
  regardless of their position in the rule structure;

* a subrule higher in the rule structure has precedence over a subrule lower in the rule structure.

These criteria induce a total order on subrules,
making the process totally deterministic.