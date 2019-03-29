Composite methods
=================

Composite methods are useful to name a given combination of other methods,
in order to make this combination reusable.

There are two distinct methods in this category.
Both are currently experimental, and have the following limitations.

.. warning::

  * They create intermediate traces named ``_x_name`` where ``x`` is a number,
    and ``name`` is the name of the computed trace using the combined method.

  * These intermediate traces are currently like any other trace in the base;
    they can be read, modified, or even deleted.
    Of course, tampering with them is unadvisable,
    as composite methods are not robust to such unexpected changes.

  * When a computed trace using a composite method is deleted,
    the intermediate traces are not cleaned up;
    they must be deleted manually.

  * For the moment, composite methods do not allow to set parameters in their component methods.

All composite methods have a required parameter ``method``,
which is the list of methods that it combines.
It is encoded as a space-separated list of absolute URIs.

Pipe
++++

This method applies the component methods in sequence.

:sources: any number
:parameters:
  :methods: a space-separated list of absolute URIs
:extensible: no

Unlike most methods,
the ``pipe`` method does not accept the ``model`` or ``origin`` parameters,
as those are specified by the last component method.

Parallel
++++++++

This method applies the component methods in parallel,
and merges all resulting traces.

:sources: any number
:parameters:
  :methods: a space-separated list of absolute URIs
  :model: the model of the computed trace
  :origin: the origin of the computed trace
:extensible: no

The ``model`` and ``origin`` parameters are handled exactly as the
`fusion`:doc: method does it;
they are required whenever the outcome of the component methods have a different model
(resp. origin).