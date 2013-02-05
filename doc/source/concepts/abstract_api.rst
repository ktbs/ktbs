.. _abstract-ktbs-api:

Abstract KTBS API
=================

Below is a language independant API that has been designed to document the functionalities of KTBS in a programmer-friendly way, and guide the implementers of client APIs in other languages.

.. warning:: TODO

  * traceBegin and traceEnd on storedTraces


Resource
--------

.. function:: get_id()

    Return the URI of this resource relative to its "containing"
    resource; basically, this is short 'id' that could have been used
    to create this resource in the corresponding 'create_X' method

    :rtype: str

.. function:: get_uri()

    Return the absolute URI of this resource.

    :rtype: uri

.. function:: force_state_refresh()

    Ensure this resource is up-to-date.
    While remote resources are expected to perform best-effort to keep in sync
    with the server, it may sometimes be required to strongly ensure they are
    up-to-date.

    For local resources, this is has obviously no effect.

.. function:: get_readonly()

    Return true if this resource is not modifiable.

    :rtype: bool

.. function:: remove()

    Remove this resource from the KTBS.
    If the resource can not be removed, an exception must be raised.

.. function:: get_label()

    Returns a user-friendly label

    :rtype: str

.. function:: set_label(str)

    Set a user-friendly label.

.. function:: reset_label()

    Reset the user-friendly label to its default value.


Ktbs (Resource)
---------------

.. function:: list_builtin_methods()

    List the builtin methods supported by the kTBS.

    :rtype: [Method]

.. function:: get_builtin_method(uri:str)

    Return the builtin method identified by the given URI if supported,
    or null.

    :rtype: Method

.. function:: list_bases()

    :rtype: [Base]

.. function:: get_base(id:uri)

    Return the trace base identified by the given URI, or null.

    :rtype: Base

.. function:: create_base(id:uri?, label:str?)

    :rtype: Base

    
Base (Base)
-----------

.. function:: get(id:uri)

    Return the element of this base identified by the given URI, or null.

    :rtype: Trace|Model|Method

.. function:: list_traces()

    :rtype: [Trace]

.. function:: list_models()

    List the models stored in that base.

    :rtype: [Model]

.. function:: create_stored_trace(id:uri?, model:Model, origin:str?, default_subject:str?, label:str?, )

    Creates a stored trace in that base
    If origin is not specified, a fresh opaque string is generated

    :rtype: StoredTrace

.. function:: create_computed_trace(id:uri?, method:Method, parameters:[str=>any]?, sources:[Trace]?, label:str?, )

    Creates a computed trace in that base.

    :rtype: ComputedTrace

.. function:: create_model(id:uri?, parents:[Model]?, label:str?)

    :rtype: Model

.. function:: create_method(id:uri, parent:Method, parameters:[str=>any]?, label:str?)

    :rtype: Method

    
Trace (Resource)
----------------

.. function:: get_base()

    :rtype: Base

.. function:: get_model()

    :rtype: Model

.. function:: get_origin()

    An opaque string representing the temporal origin of the trace:
    two traces with the same origin can be temporally compared.

    :rtype: str

.. function:: list_source_traces()

    :rtype: [Trace]

.. function:: list_transformed_traces()

    Return the list of the traces of which this trace is a source.

    :rtype: [Trace]

.. function:: list_obsels(begin:int?, end:int?, reverse:bool?)

    Return a list of the obsel of this trace matching the parameters.

    :rtype: [Obsel]

.. function:: get_obsel(id:uri)

    Return the obsel of this trace identified by the URI, or null.

    :rtype: Obsel

    
StoredTrace (Trace)
-------------------

.. function:: set_model(model:Model)

.. function:: set_origin(origin:str)

.. function:: get_default_subject()

    The default subject is associated to new obsels if they do not specify
    a subject at creation time.

    :rtype: str

.. function:: set_default_subject(subject:str)

.. function:: create_obsel(id:uri?, type:ObselType, begin:int, end:int?, subject:str?, \
              attributes:[AttributeType=>any]?, \
              relations:[(RelationType, Obsel)]?, \
              inverse_relations:[(Obsel, RelationType)]?, \
              source_obsels:[Obsel]?, label:str?)

    :rtype: Obsel

 
ComputedTrace(Trace)
--------------------

.. function:: get_method()

    :rtype:  Method

.. function:: set_method(method:Method)

.. function:: list_parameters(include_inherited:bool?)

    List the names of all the parameters of this trace.

    :param include_inherited: defaults to true and means that parameters inherited
                              from the method should be included
    :rtype: [str]

.. function:: get_parameter(key:str)

    Get the value of a parameter (own or inherited from the method).

    :rtype: str

.. function:: set_parameter(key:str, value:any)

    Set the value of a parameter.
    An exception must be raised if the parameter is inherited.

.. function:: del_parameter(key:str)

    Unset a parameter.
    An exception must be raised if the parameter is inherited.

    
Model (Resource)
----------------

.. function:: get_base()

    :rtype: Base

.. function:: get_unit()

    TODO find stable reference to unit names

    :rtype: str

.. function:: set_unit(unit:str)

.. function:: get(id:uri)

    Return the element of this model identified by the URI, or null.

    :rtype: ObselType | AttributeType | RelationType

.. function:: list_parents(include_indirect:bool?)

    List parent models.
    Note that some of these models may not belong to the same KTBS, and may
    be readonly —see get_readonly.

    :param include_indirect: defaults to false and means that parent's parents should
                             be returned as well.
    :rtype: [Model]

.. function:: list_attribute_types(include_inherited:bool?)

    :param include_inherited: defaults to true and means that attributes types
                              from inherited models should be included
    :rtype: [AttributeType]

.. function:: list_relation_types(include_inherited:bool?)

    :param include_inherited: defaults to true and means that relation types
                              from inherited models should be included
    :rtype: [RelationType]

.. function:: list_obsel_types(include_inherited:bool?)

    :param include_inherited: defaults to true and means that obsel types
                              from inherited models should be included
    :rtype: [ObselType]

.. function:: add_parent(m:Model)

.. function:: remove_parent(m:Model)

.. function:: create_obsel_type(id:uri?, supertypes:[ObselType]?, label:str)

    NB: if id is not provided, label is used to mint a human-friendly URI

    :rtype: ObselType

.. function:: create_attribute_type(id:uri?, obsel_type:ObselType?, data_type:uri?, \
              value_is_list:bool?, label:str)

    NB: if data_type represent a "list datatype", value_is_list must not be
    true
    NB: if id is not provided, label is used to mint a human-friendly URI
    TODO specify a minimum list of datatypes that must be supported
    TODO define a URI for representing "list of X" for each supported datatype

    :param data_type: uri is an XML-Schema datatype URI.
    :param value_is_list: indicates whether the attributes accepts a single value
                          (false, default) or a list of values (true).
    :rtype: AttributeType

.. function:: create_relation_type(id:uri?, origin:ObselType?, destination:ObselType?, \
              supertypes:[RelationType]?, label:str)

    NB: if id is not provided, label is used to mint a human-friendly URI

    :rtype: RelationType

    
    
Method (Resource)
-----------------

.. function:: get_base()

    :rtype: Base

.. function:: get_parent()

    Return the parent method, or null.
    Note that returned method may not be stored on this KTBS, or can even be
    a built-in method.

    :rtype: Method

.. function:: set_parent(method:Method)

.. function:: list_parameters(include_inherited:bool?)

    List the names of all the parameters set by this method or its parent.

    :param include_inherited: defaults to true and means that parameters from the
                              parent method should be included
    :rtype: [str]

.. function:: get_parameter(key:str)

    Get the value of a parameter (own or inherited from the parent method).

    :rtype: str

.. function:: set_parameter(key:str, value:any)

    set the value of a parameter.
    An exception must be raised if the parameter is inherited.

.. function:: del_parameter(key:str)

    Unset a parameter.
    An exception must be raised if the parameter is inherited.

    
ObselType (Resource)
--------------------

.. function:: get_model()

    :rtype: Model

.. function:: list_supertypes(include_indirect:bool?)

    List the supertypes of this obsel type.

    :param include_indirect: defaults to false; if true, all supertypes are listed,
                             including indirect supertypes and this obsel type itself
    :rtype: [ObselType]

.. function:: list_subtypes(include_indirect:bool?)

    List the subtypes of this obsel type from the same model.

    :param include_indirect: defaults to false; if true, all subtypes from the same
                             model are listed, including indirect supertypes and this 
                             obsel type itself
    :rtype: [ObselType]

.. function:: list_attribute_types(include_inherited:bool?)

    List the attribute types of this obsel type (direct or inherited).

    :param include_inherited: defaults to true and means that attributes types
                              inherited from supertypes should be included
    :rtype: [AttributeType]

.. function:: list_relation_types(include_inherited:bool?)

    List the outgoing relation types of this obsel type (direct or inherited).

    :param include_inherited: defaults to true and means that relation types
                              inherited from supertypes should be included
    :rtype: [RelationType]

.. function:: list_inverse_relation_types(include_inherited:bool?)

    List the inverse relation types of this obsel type (direct or inherited).

    :param include_inherited: defaults to true and means that inverse relation types
                              inherited from supertypes should be included
    :rtype: [RelationType]

.. function:: create_attribute_type(id:uri?, data_type:uri?, value_is_list:book?, \
              label:str)

    Shortcut to get_model().create_attribute_type where this ObselType is the
    obsel type.

    :rtype: AttributeType

.. function:: create_relation_type(id:uri?, destination:ObselType?, \
              supertypes:[RelationType]?, label:str)

    Shortcut to get_model().create_relation_type where this ObselType is the
    origin.

    :rtype: RelationType

.. function:: add_supertype(ot:ObselType)

.. function:: remove_supertype(ot:ObselType)

      
    
AttributeType (Resource)
------------------------

.. function:: get_model()

    :rtype: Model

.. function:: get_obsel_type()

    :rtype: ObselType

.. function:: set_obsel_type(ot:ObselType)

.. function:: get_data_type()

    :rtype: uri

.. function:: set_data_type(data_type:uri, is_list:bool?)

    NB: if data_type represent a "list datatype", value_is_list must not be
    true

    :param is_list: indicates whether the attribute accepts a single value (false,
                    default) or a list of values (true)
    :rtype: 

    
RelationType (Resource)
-----------------------

.. function:: get_model()

    :rtype: Model

.. function:: list_supertypes(include_indirect:bool?)

    List the supertypes of this relation type.

    :param include_indirect: defaults to false; if true, all supertypes are listed,
                             including indirect supertypes and this relation type itself
    :rtype: [RelationType]

.. function:: list_subtypes(include_indirect:bool?)

    List the subtypes of this relation type from the same model.

    :param include_indirect: defaults to false; if true, all subtypes from the same
                             model are listed, including indirect supertypes and this 
                             relation type itself
    :rtype: [RelationType]

.. function:: get_origin()

    :rtype: ObselType

.. function:: set_origin(ot:ObselType)

.. function:: get_destination()

    :rtype: ObselType

.. function:: set_destination(ot:ObselType)

.. function:: add_supertype(rt:RelationType)

.. function:: remove_supertype(rt:RelationType)


    
Obsel (Resource)
----------------

.. function:: get_trace()

    :rtype: Trace

.. function:: get_obsel_type()

    :rtype: ObselType

.. function:: get_begin()

    :rtype: int

.. function:: get_end()

    :rtype: int

.. function:: list_source_obsels()

    :rtype: [Obsel]

.. function:: list_attribute_types()

    :rtype: [AttributeType]

.. function:: list_relation_types()

    :rtype: [RelationType]

.. function:: list_related_obsels(rt:RelationType)

    :rtype: [Obsel]

.. function:: list_inverse_relation_types()

    :rtype: [RelationTtype]

.. function:: get_attribute_value(at:AttributeType)

    Return the value of the given attribute type for this obsel.

    :rtype: any

Obsel modification (trace amendment)

.. function:: set_attribute_value(at:AttributeType, value:any)

.. function:: del_attribute_value(at:AttributeType)

.. function:: add_related_obsel(rt:RelationType, value:Obsel)

.. function:: del_related_obsel(rt:RelationType, value:Obsel)


    
General Rules
-------------

* Whenever parameter is named 'id:uri', it must be possible to provide a
  relative URI, which will be resolved against the URI of the target object.

* The order of the parameter is important. Whenever an optional parameter is to
  be omitted, it can be set to NULL or named parameters (language permitting)
  can be used for the following parameters.

* For all get_X methods accepting a parameter, the result should be null if no
  object matches the parameter.

* For all create_X methods, an exception must be raised if the given URI is
  invalid or already in use.

* All modification operations (set_*, remove) on model elements (ObselType,
  AttributeType, RelationType) actually modify the model from which they were
  accessed. If the model is readonly (see the get_readonly method), those
  methods must raise an exception.


Design Rationale
----------------

* As method-controlled attributes are not possible or easy to implement in some/
  languages, this abstract API only defines *methods*, in order to provide the
  least common denominator.

* For the same reason, whenever mutiple values are to be returned, it
  prescribes the use of a list (or the closest match in the target language,
  e.g. Array in javascript).

* However, adaptations are also recommended, depending on the features of the
  target language. All those adaptations should be documented with the given
  API. Below is a list of recommended adaptations:

  * for languages supporting read-only attributes, it is recommended
    to provide a read-only attribute 'x' for every method get_x(); if get_x
    has optional parameters, 'x' should be equivalent to calling it with 0
    parameters.

    It is also recommended to provide a read-only attribute 'xs' for every
    method list_xs(); if list_xs has optional parameters, 'xs' should be
    equivalent to calling it with 0 parameters.

  * for languages supporting method-controlled attributes, it is recommended
    to make attribute 'x' settable whenever there is a method set_x(val);
    if set_x has additional optional parameters, 'x' should be equivalent to
    calling it with only the first parameter.

  * for language supporting a notion of iterator (which may be more efficient
    than lists), it is recommended to provide a method iter_xs(...) for every
    method list_xs(...), acceptin the same parameters.

    NB: implementing list_xs(...) on top of iter_xs(...) should be trivial,
    and would probably be the way to do. 

  * for language having a tradition of using CamelCase instead of underscore,
    all method may be renamed by replacing _[a-z] with the corresponding
    capital letter.
