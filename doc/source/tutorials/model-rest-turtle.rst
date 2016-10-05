Describing a model in Turtle
============================

This tutorial explains how to describe a trace model for kTBS.

Preparation
-----------

First, you have to create a new base as described in the :ref:`REST tutorial<ktbs-rest-turtle-tutorial>`. We will assume that this base is named ``http://localhost:8001/base01/``.


Running example
---------------

Here is a UML representation of the Trace Model we will create. This is a minimal trace model of a typical online chat activity.

.. graphviz::

   digraph {
     rankdir = RL
     node [ shape = "record", fontsize = 8 ]
     edge [ fontsize = 8, arrowhead = "open" ]

     EnterChatRoom [ label = "EnterChatRoom|room:string" ]
     SendMsg [ label = "SendMsg|message:string" ]
     MsgReceived [ label = "MsgResseived|message:string\lfrom:string\l" ]
     LeaveRoom [ label = "LeaveRoom|" ]

     SendMsg -> EnterChatRoom [ label = "inRoom" ]
     MsgReceived -> EnterChatRoom [ label = "inRoom" ]
     LeaveRoom -> EnterChatRoom [ label = "inRoom" ]

   }


Creating the model
------------------

On the page of your base,
select the POST request, the ``text/turtle`` content type,
and copy the following data in the text area:

.. code-block:: turtle

   @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .

   <.> :contains <model1> .
   <model1> a :TraceModel .

then press the ``Send`` button.
The model is created and
is now available at http://localhost:8001/base1/model1 .

If you visit that IRI,
you will notice that the new model has an additional property:
``:hasUnit :millisecond``.
Every trace model must have a unit,
specifying how time will be represented in the traces complying with this model
(see `../concepts/trace_time_management`:doc:).


Modifying the model
-------------------

Creating obsel types
^^^^^^^^^^^^^^^^^^^^

We will first create the obsel types.
Visit the model at http://localhost:8001/base1/model1 ,
select the PUT request, the ``text/turtle`` content type,
and modify the code with the following:

.. code-block:: turtle

   @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .
   @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.

   <.> :contains <model1> .

   <model1> a :TraceModel ;
       :hasUnit :millisecond .

   <#EnterChatRoom> a :ObselType .
   <#SendMsg> a :ObselType .
   <#MsgReceived> a :ObselType .
   <#LeaveRoom> a :ObselType .

then press the ``Send`` button.
The page should reload and show the new obsel types.

.. note::

   Note that all relative IRIs in this example are interpreted against the IRI *of the model*
   (as it is the target IRI of the PUT request).
   For the sake of readability, we keep ``<model1>`` to identify the model itsel,
   but ``<>`` would work as well.
   All components of the models have their IRI starting with ``#``,
   so ``<#EnterChatRoom>`` is a shorthand for ``<http://localhost:8001/base1/model1#EnterChatRoom>``,
   for example.

   Note that you could not have POSTed the Turtle code above as is,
   as relative IRIs in a POST are interpreted against the IRI of the *base*
   (``<http://localhost:8001/base01/>`` in this case).

   It is still possible to create the obsel types together with the model at POST time,
   but then you need change the relative IRIs accordingly,
   ``<model1#EnterChatRoom>`` instead of ``<#EnterChatRoom>``, etc.

Adding attributes
^^^^^^^^^^^^^^^^^

We will now associate attributes to our newly created obsel types.

As obsel types, each attribute has a unique IRI, relative to that of the model:
``<#room>``, ``<#message>`` and ``<#from>``.
It is related to the obsel type(s) in which it may appear by the ``:hasAttributeDomaine`` property.

The datatype of an attribute is specified using ``:hasAttributeRange``. kTBS supports a subset of the primitive datatypes defined in  XML-Schema_, including the most usual datatypes such as ``xsd:string``, ``xsd:integer``, ``xsd:boolean`` and ``xsd:float``.

.. _XML-Schema: http://www.w3.org/TR/xmlschema-2/#built-in-datatypes

.. code-block:: turtle

   @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .
   @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
   @prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

   <.> :contains <model1> .

   <model1> a :TraceModel ;
       :hasUnit :millisecond .

   <#EnterChatRoom> a :ObselType .
   <#SendMsg> a :ObselType .
   <#MsgReceived> a :ObselType .
   <#LeaveRoom> a :ObselType .

   <#room> a :AttributeType ;
       skos:prefLabel "room" ;
       :hasAttributeDomain <#EnterChatRoom> ;
       :hasAttributeRange xsd:string .

   <#message> a :AttributeType ;
       skos:prefLabel "message" ;
       :hasAttributeDomain <#SendMsg>, <#MsgReceived> ;
       :hasAttributeRange xsd:string .

   <#from> a :AttributeType ;
       skos:prefLabel "from" ;
       :hasAttributeDomain <#MsgReceived> ;
       :hasAttributeRange xsd:string .

.. note::

   In UML, attributes belong to a given class,
   and their name is scoped to that class.
   It is therefore possible to have two different classes ``A`` and ``B``,
   both having an attribute named ``foo``,
   and still have ``A.foo`` mean something completely different from ``B.foo``
   (they could for example have different datatypes).

   In kTBS on the other hand,
   attributes are first-class citizens of the model,
   their name (IRI) is scoped to the entire model.
   In our example above, the attribute ``<#message>`` is shared by two obsel types,
   it is therefore the *same* attribute,
   with the same meaning and the same datatype\ [#abstract_class]_.

   If we wanted to consider ``SendMsg.message`` and ``MsgReceived.message`` as two distinct attributes
   more in the line of UML design,
   then we would need to create two attribute types with distinct IRIs,
   for example ``<#SendMsg/message>`` and ``<#MsgReceived/message>``.



Adding relations
^^^^^^^^^^^^^^^^

We now define the types of relation that may exist between obsels in our model.
Just like obsel types and attributes,
relation types are named with an IRI relative to that of the model.
The type(s) of the obsels from which the relation can originate is specified with ``:hasRelationDomain``.
The type(s) of the obsels to which the relation can point is specified with ``:hasRelationRange``.

.. code-block:: turtle

   @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .
   @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
   @prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

   <.> :contains <model1> .

   <model1> a :TraceModel ;
       :hasUnit :millisecond .

   <#EnterChatRoom> a :ObselType .
   <#SendMsg> a :ObselType .
   <#MsgReceived> a :ObselType .
   <#LeaveRoom> a :ObselType .

   <#room> a :AttributeType ;
       skos:prefLabel "room" ;
       :hasAttributeDomain <#EnterChatRoom> ;
       :hasAttributeRange xsd:string .

   <#message> a :AttributeType ;
       skos:prefLabel "message" ;
       :hasAttributeDomain <#SendMsg>, <#MsgReceived> ;
       :hasAttributeRange xsd:string .

   <#from> a :AttributeType ;
       skos:prefLabel "from" ;
       :hasAttributeDomain <#MsgReceived> ;
       :hasAttributeRange xsd:string .

   <#inRoom> a :RelationType ;
       :hasRelationDomain <#SendMsg>, <#MsgReceived>, <#LeaveRoom> ;
       :hasRelationRange <#EnterChatRoom> .


.. _inheritance:

Inheritance of obsel types
^^^^^^^^^^^^^^^^^^^^^^^^^^

While we can be satisfied with the model above and keep it that way,
we can also notice that obsel types ``SendMsg`` and ``MsgReceived`` share a lot of things
(namely the attribute ``message`` and being in the domain of ``inRoom``).
This creates some redundancy in the model definition.

To avoid that redundancy,
and capture explicitly the commonalities between those obsel types,
we can refactor those commonalities into a new obsel type ``MsgEvent``
which both ``SendMsg`` and ``MsgReceived`` would inherit.

.. code-block:: turtle

   @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .
   @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
   @prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

   <.> :contains <model1> .

   <model1> a :TraceModel ;
       :hasUnit :millisecond .

   <#EnterChatRoom> a :ObselType .
   <#MsgEvent> a :ObselType .
   <#SendMsg> a :ObselType ;
       :hasSuperObselType <#MsgEvent> .
   <#MsgReceived> a :ObselType ;
       :hasSuperObselType <#MsgEvent> .
   <#LeaveRoom> a :ObselType .

   <#room> a :AttributeType ;
       skos:prefLabel "room" ;
       :hasAttributeDomain <#EnterChatRoom> ;
       :hasAttributeRange xsd:string .

   <#message> a :AttributeType ;
       skos:prefLabel "message" ;
       :hasAttributeDomain <#MsgEvent> ;
       :hasAttributeRange xsd:string .

   <#from> a :AttributeType ;
       skos:prefLabel "from" ;
       :hasAttributeDomain <#MsgReceived> ;
       :hasAttributeRange xsd:string .

   <#inRoom> a :RelationType ;
       :hasRelationDomain <#MsgEvent>, <#LeaveRoom> ;
       :hasRelationRange <#EnterChatRoom> .

This new trace model can be represented by the following UML diagram:

.. graphviz::

   digraph {
     rankdir = RL
     node [ shape = "record", fontsize = 8 ]
     edge [ fontsize = 8 , arrowhead = "open", spines = false ]

     EnterChatRoom [ label = "EnterChatRoom|room:string" ]
     MsgEvent [ label = "MsgEvent|message:string" ]
     SendMsg [ label = "SendMsg|" ]
     MsgReceived [ label = "MsgResseived|from:string" ]
     LeaveRoom [ label = "LeaveRoom|" ]

     MsgEvent -> EnterChatRoom [ label = "inRoom" ]
     LeaveRoom -> EnterChatRoom [ label = "inRoom" ]
     SendMsg -> MsgEvent [ arrowhead = "empty" ]
     MsgReceived -> MsgEvent [ arrowhead = "empty" ]

   }


.. rubric:: Footnotes

.. [#abstract_class] In order to achieve this in UML,
   we would need an abstract class (*e.g.* ``WithMessage``)
   defining the attribute ``message``,
   and have both classes ``SendMsg`` and ``MsgReceived`` inherit that abstract class.

   Note that this design is still possible with kTBS,
   and can be useful when multiple attributes and/or relations are shared together in several obsel types
   (see (using `inheritance`:ref:).
