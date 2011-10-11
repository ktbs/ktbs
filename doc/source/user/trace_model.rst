Trace Model
===========

A trace model defines the following elements:

* a hierarchy of obsel types,
* attributes that obsels of each type can have,
* relations that can exist between obsels of each type.

In the future, the trace model will also define the time-unit to be used in the corresponding traces. For the moment, the only supported unit is the millisecond.

The obsel types are organised in a specialisation hierarchy: each obsel of a subtype also belongs to the supertype. As a consequence, attributes and relations are inherited from a supertype by its subtypes.

Note also that relations are also structured in a specialisation hierarchy.

In the future, it will be possible for a model to import another model; this will allow a model to refine another one, or modular models to be combined into complex ones. For the moment, this is possible by copy-pasting models into each others. 

Model validation
----------------

A trace complies with its model if the following conditions are met:

* every obsel has an obsel type belonging to the model;
* every attribute belongs to an obsel whose type is (a subtype of) the domain of that attribute;
* every relation links two obsels whose type are (a subtype of) the domain and range (respectively) of the relation.

Note that there is no way for the moment to restrict the cardinality of attributes or relations: any attribute or relation may be omitted or repeated.

Note that traces are allowed not to comply with their model; kTBS will not prevent the creation of an obsel or the amendment of a trace causing it to be non-compliant.
