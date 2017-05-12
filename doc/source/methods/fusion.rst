Fusion
======

This method merges the content of all its sources.

:sources: any number
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
:extensible: no

If all source traces have the same model (resp. origin),
then parameter ``model`` (resp. ``origin``) is not required,
and in that case the computed trace will have
the same model (resp. origin) as its source(s).
