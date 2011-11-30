.. _abstract-ktbs-api:

Abstract KTBS API
=================

Below is a language independant API that has been designed to document the functionalities of KTBS in a programmer-friendly way, and guide the implementers of client APIs in other languages.

.. warning:: TODO

  * traceBegin and traceEnd on storedTraces
  * multiple values for a relation on an obsel

::

    Resource
      get_uri() → uri
      get_sync_status() → str
          return "ok" if the resource is in sync with the data at its URI,
          else any other string describing the reason why it is not.
      get_readonly() → bool
          return true if this resource is not modifiable
      remove()
          remove this resource from the KTBS
          If the resource can not be removed, an exception must be raised.
      get_label() → str
          returns a user-friendly label
      set_label(str)
          set a user-friendly label
      reset_label()
          reset the user-friendly label to its default value
      
    
    Ktbs (Resource)
      list_bases() → [Base]
      get_base(id:uri) → Base
          return the trace base identified by the given URI, or null
      create_base(label:str?, id:uri?) → Base
      list_builtin_methods() → [Method]
          list the builtin methods supported by the kTBS
       
    
    Base (Base)
      get(id:uri) → Trace|Model|Method|ObselType|AttributeType|RelationType|Obsel
          return the element of this base identified by the given URI, or null
      list_traces() → [Trace]
      list_models() → [Model]
          list the models stored in that base
      list_methods() → [Method]
          list the methods stored in that base
      create_stored_trace(model:Model, origin:str?, default_subject:str?,
                          label:str?, id:uri?)
                         → StoredTrace
          list the stored traces stored in that base
          if origin is not specified, a fresh opaque string is generated
      create_computed_trace(method:Method, sources:[Trace]?, label:str?, id:uri?)
                           → ComputedTrace
          list the computed traces stored in that base
      create_model(parents:[Model]?, label:str?, id:uri?) → Model
      create_method(parent:Method, parameters:[str=>any]?, label:str?,
                    id:uri) → Method
    
    Trace (Resource)
      get_base() → Base
      get_model() → Model
      get_origin() → str
          an opaque string representing the temporal origin of the trace:
          two traces with the same origin can be temporally compared
      list_source_traces() → [Trace]
      list_transformed_traces() → [Trace]
          return the list of the traces of which this trace is a source
      list_obsels(begin:int?, end:int?, reverse:bool?) → [Obsel]
          return a list of the obsel of this trace matching the parameters
      get_obsel(id:uri) → Obsel
          return the obsel of this trace identified by the URI, or null
    
    StoredTrace (Trace)
      set_model(model:Model)
      set_origin(origin:str)
      get_default_subject() → str
          the default subject is associated to new obsels if they do not specify
          a subject at creation time
      set_default_subject(subject:str)
      create_obsel(type:ObselType, begin:int, end:int?, subject:str?,
                   attributes:[AttributeType=>any]?,
                   relations:[RelationType=>Obsel]?,
                   inverse_relations:[RelationType=>Obsel]?,
                   source_obsels:[Obsel]?, label:str?, id:uri?) → Obsel
    
    ComputedTrace(Trace)
      get_method() → Method
      set_method(method:Method)
      list_parameters(include_inherited:bool?) → [str]
          list the names of all the parameters of this trace
          include_inherited defaults to true and means that parameters inherited
          from the method should be included
      get_parameter(key:str) → str
          get the value of a parameter (own or inherited from the method)
      set_parameter(key:str, value:any)
          set the value of a parameter
          An exception must be raised if the parameter is inherited.
      del_parameter(key:str)
          unset a parameter
          An exception must be raised if the parameter is inherited.
    
    Model (Resource)
      get_base() → Base
      get_unit() → str
          TODO find stable reference to unit names
      set_unit(unit:str)
      get(id:uri) → ObselType | AttributeType | RelationType
          return the element of this model identified by the URI, or null
      list_parents(include_indirect:bool?) → [Model]
          list parent models
          Note that some of these models may not belong to the same KTBS, and may
          be readonly —see get_readonly.
          include_indirect defaults to false and means that parent's parents should
          be returned as well.
      list_attribute_types(include_inherited:bool?) → [AttributeType]
          include_inherited defaults to true and means that attributes types
          from inherited models should be included
      list_relation_types(include_inherited:bool?) → [RelationType]
          include_inherited defaults to true and means that relation types
          from inherited models should be included
      list_obsel_types(include_inherited:bool?) → [ObselType]
          include_inherited defaults to true and means that obsel types
          from inherited models should be included
    
      add_parent(m:Model)
      remove_parent(m:Model)
      create_obsel_type(label:str, supertypes:[ObselType]?, id:uri?) → ObselType
          NB: if id is not provided, label is used to mint a human-friendly URI
      create_attribute_type(label:str, obsel_type:ObselType?, data_type:uri?,
                            value_is_list:bool?, id:uri?) → AttributeType
          the data_type uri is an XML-Schema datatype URI;
          value_is_list indicates whether the attributes accepts a single value
          (false, default) or a list of values (true).
          NB: if data_type represent a "list datatype", value_is_list must not be
          true
          NB: if id is not provided, label is used to mint a human-friendly URI
          TODO specify a minimum list of datatypes that must be supported
          TODO define a URI for representing "list of X" for each supported datatype
      create_relation_type(label:str, origin:ObselType?, destination:ObselType?,
                           supertypes:[RelationType]?, id:uri?) → RelationType
          NB: if id is not provided, label is used to mint a human-friendly URI
    
    
    Method (Resource)
      get_base() → Base
      get_parent() → Method
          return the parent method, or null
          Note that returned method may not be stored on this KTBS, or can even be
          a built-in method.
      set_parent(method:Method)
      list_parameters(include_inherited:bool?) → [str]
          list the names of all the parameters set by this method or its parent
          include_inherited defaults to true and means that parameters from the
          parent method should be included
      get_parameter(key:str) → str
          get the value of a parameter (own or inherited from the parent method)
      set_parameter(key:str, value:any)
          set the value of a parameter
          An exception must be raised if the parameter is inherited.
      del_parameter(key:str)
          unset a parameter
          An exception must be raised if the parameter is inherited.
    
    ObselType (Resource)
      get_model() → Model
      list_supertypes(include_indirect:bool?) → [ObselType]
          list the supertypes of this obsel type
          include_indirect defaults to false; if true, all supertypes are listed,
          including indirect supertypes and this obsel type itself
      list_subtypes(include_indirect:bool?) → [ObselType]
          list the subtypes of this obsel type from the same model
          include_indirect defaults to false; if true, all subtypes from the same
          model are listed, including indirect supertypes and this obsel type
          itself
      list_attribute_types(include_inherited:bool?) → [AttributeType]
          list the attribute types of this obsel type (direct or inherited)
          include_inherited defaults to true and means that attributes types
          inherited from supertypes should be included
      list_relation_types(include_inherited:bool?) → [RelationType]
          list the outgoing relation types of this obsel type (direct or inherited)
          include_inherited defaults to true and means that relation types
          inherited from supertypes should be included
      list_inverse_relation_types(include_inherited:bool?) → [RelationType]
          list the inverse relation types of this obsel type (direct or inherited)
          include_inherited defaults to true and means that inverse relation types
          inherited from supertypes should be included
      create_attribute_type(label:str, data_type:uri?, value_is_list:book?,
                            id:uri?)
                           → AttributeType
          shortcut to get_model().create_attribute_type where this ObselType is the
          obsel type
      create_relation_type(label:str, destination:ObselType?,
                           supertypes:[RelationType]?, id:uri?)
                          → RelationType
          shortcut to get_model().create_relation_type where this ObselType is the
          origin
      add_supertype(ot:ObselType)
      remove_supertype(ot:ObselType)
      
    
    AttributeType (Resource)
      get_model() → Model
      get_obsel_type() → ObselType
      set_obsel_type(ot:ObselType)
      get_data_type() → uri
      set_data_type(data_type:uri, is_list:bool?)
          is_list indicates whether the attribute accepts a single value (false,
          default) or a list of values (true)
          NB: if data_type represent a "list datatype", value_is_list must not be
          true
    
    RelationType (Resource)
      get_model() → Model
      list_supertypes(include_indirect:bool?) → [RelationType]
          list the supertypes of this relation type
          include_indirect defaults to false; if true, all supertypes are listed,
          including indirect supertypes and this relation type itself
      list_subtypes(include_indirect:bool?) → [RelationType]
          list the subtypes of this relation type from the same model
          include_indirect defaults to false; if true, all subtypes from the same
          model are listed, including indirect supertypes and this relation type
          itself
      get_origin() → ObselType
      set_origin(ot:ObselType)
      get_destination() → ObselType
      set_destination(ot:ObselType)
      add_supertype(rt:RelationType)
      remove_supertype(rt:RelationType)
    
    Obsel (Resource)
      get_trace() → Trace
      get_obsel_type() → ObselType
      get_begin() → int
      get_end() → int
      get_subject() → str
      list_source_obsels() → [Obsel]
      list_attribute_types() → [AttributeType]
      list_relation_types() → [RelationType]
      list_related_obsels(rt:RelationType) → [Obsel]
      list_inverse_relation_types() → [RelationTtype]
      list_relating_obsels(rt:RelationType) → [Obsel]
      get_attribute_value(at:AttributeType) → any
          return the value of the given attribute type for this obsel
      # obsel modification (trace amendment)
      set_attribute_value(at:AttributeType, value:any)
      del_attribute_value(at:AttributeType)
      add_related_obsel(rt:RelationType, value:Obsel)
      del_related_obsel(rt:RelationType, value:Obsel)
    
General Rules
-------------

* Whenever parameter is named 'id:uri', it should be possible to provide a
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
