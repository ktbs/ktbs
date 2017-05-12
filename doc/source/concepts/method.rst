Method
======

A method is used by a `computed trace <concept-computed-trace>`:ref:
to determine its model and origin,
and to generate its obsels.
The kTBS provides a number of `built-in methods <../methods>`:doc:.
It is also possible to create user-defined methods,
that are stored in a base besides trace models and traces.

User-defined methods
--------------------

A user defined method is described by:

* an inherited method (either built-in or user-defined),
* a number of parameters.

For simple methods such as filter, this is merely a way to define a reusable set of parameters. However, for more generic method such as Sparql or External, it provides a mean to encapsulate a complex transformation, possibly requiring its own parameters (via extensibility). 
