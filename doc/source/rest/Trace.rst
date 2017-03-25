Trace
=====

This class is the base class of `StoredTrace`:doc: and `ComputedTrace`:doc:. It has no direct instances (only the two subclasses above can be instantiated), but everything described here is valid for any indirect instance.

Traces have one :ref:`aspect resource <rest-aspect-resource>`:

* `@obsels`_, linked through http://liris.cnrs.fr/silex/2009/ktbs#hasObselCollection

Original resource
+++++++++++++++++

GET
---

Retrieve the description of the trace, augmented with the following generated properties:

* http://liris.cnrs.fr/silex/2009/ktbs#compliesWithModel can be either "yes", "no" or "?" (if the model is not available)
* links to the @obsel aspect resource.

PUT
---

This allows to change the description of the trace itself.

DELETE
------

Deletes the trace and its aspect resources.

TODO: what happens if the trace is the source of a computed trace?

Description Constraints
-----------------------

The description of a trace must be `star shaped <star-shaped>`:ref:.


@obsels
+++++++

This aspect resource stands for the obsel collection of the trace.

GET
---

Return the description of all the obsels of the trace.
This description can be filtered by passing the following query-string arguments:

  :after: an obsel URI, only obsels after this one will be returned
  :before: an obsel URI, only obsels before this one will be returned
  :limit: an int, only that many obsels (at most) will be returned
  :minb: an int, the minimum begin value for returned obsels
  :mine: an int, the minimum end value for returned obsels
  :maxb: an int, the maximum begin value for returned obsels
  :maxe: an int, the maximum end value for returned obsels
  :offset: an int, skip that many obsels
  :reverse: a boolean\ [#boolean]_, reverse the order (see below)

For example http://localhost:8001/base1/t01/@obsels?minb=42&maxe=101 will return only those obsel beginning at or after 42 and ending at or before 101.
            
Some of these parameters
(``after``, ``before``, ``limit``, ``offset`` and ``reverse``)
rely on the :ref:`obsel_total_ordering`.
For example, ``@obsels?limit=10`` will return the first ten obsels,
while ``@obsels?reverse&limit=10`` will return the last ten obsels.
Remember however that most RDF serializations have no notion of order
(they convey a *set* of triples)
so the representation of those resources may appear unordered.
The JSON-LD serializer in kTBS is a notable exception:
the obsel list is sorted according to the obsel ordering.

Even with unordered serializations, however,
this still allows to retrieve obsels of a big trace in a paginated fashion,
using ``limit`` to specify the size of the page,
and ``after`` to browse from one page to another
(setting its value to the latest obsel of the previous page),
or ``before`` when paginating in the ``reverse`` order\ [#offset]_.
To make it easier,
kTBS provides a ``next`` Link HTTP header (per :rfc:`5988`)
pointing to the next page.

Representation completeness
```````````````````````````

Obsels with a complex structure (see below)
may not be entirely described in the representations of ``@obsels``.
More precisely, all attributes (*i.e.* outgoing properties) of obsels,
and all inter-obsel relations will *always* be represented.
However, if an attribute has a complex value,
represented as a blank node with its own properties,
then the representations of ``@obsels``
will usually\ [#usually]_ truncate such property paths to a length of 3.

This limitation has been introduced to ensure good performances,
and is deemed acceptable as obsels typically have a flat structure
(depth of 1), and occasionnally a depth of 2.
In order to get the full description of an obsel,
you can of course still get it from the obsel URI.

Also, note that transformation methods sill have access to the whole structure of obsels


.. [#boolean] The value is case insensitive,
   and any value different from ``false``, ``no`` or ``0`` will be considered true.
   Note that the empty string is considered true,
   so that this parameter can be used without any value,
   as in ``@obsels?reverse&limit=10``.

.. [#offset] The ``offset`` option would be simpler to use,
   but its use is not always allowed on big traces
   (for example, `Virtuoso <http://virtuoso.openlinksw.com/>`_
   forbids it beyond a certain amount of obsels),
   so using ``after``/``before`` is more robust
   (and potentially more efficient).

.. [#usually] You *may* retrieve longer paths in some situations,
   but this should not be relied upon.
