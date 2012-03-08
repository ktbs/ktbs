REST in kTBS
============

REST basic notions
------------------

The central notion in REST is the notion of *resource*. Each resource is identified by an URI and accessed through HTTP operations to that URI. Those operations manipulate *representations* of the resource; the resource itself is an abstract entity that is never directly reached.

GET:
    Return a representation of the resource.

PUT:
    Alter a resource by submitting a new representation.
   

POST:
    Creates a new resource by submitting its representation to a "parent"
    resource.

DELETE:
    Deletes a resource.

For more information on the REST architecture, refer to http://en.wikipedia.org/wiki/Representational_state_transfer.



Resource relations
------------------

kTBS uses two special relations between resources: parent/child resource and aspect resource.

Parent/child resource
+++++++++++++++++++++

Resources in kTBS are organized in a hierarchy, and every resource (except for
the :doc:`KtbsRoot`), has exactly one parent. This hierarchy is naturally
reflected by the path of the resources' URIs.

.. _child-modification:

Although the description of the parent resource may contain references to its children resource and some information about them, the general rule is that this information can not be altered by PUT requests to the parent resource. Instead, child resources are:

* created by a POST request to the parent resource;
* altered by a PUT request to themselves;
* deleted by a DELETE request to themselves.

.. _rest-aspect-resource:

Aspect resources
++++++++++++++++

Some resources are too complex to be handled only through the four HTTP verbs. Those resources are therefore linked to several *aspect resources*, each of them represeting only one aspect of the original resource.

As a convention, a resource with aspect resources will have a URI ended with '/', and all its aspect resources will have a suffix starting with '@'. The number, types and names of aspect resources depends only on the type of the original resource. Aspect resources are automatically created and deleted with the original resource and can not be created or deleted independandly.

.. admonition:: example

  A `trace <Trace>`:doc: has exactly two aspect resources called `@about` and `@obsels`. If the URI of the trace is http://example.com/ws1/t01/, the URI of the aspect resources will be http://example.com/ws1/t01/@about and http://example.com/ws1/t01/@obsels, respectively. The first one holds the metadata about the trace (date of creation, compliance with its `model <Model>`:doc:, etc.), while the second one holds its `obsel <Obsel>`:doc: collection.

Although each type defines the name of its aspect resources, it is consider a better practice to *discover* their names through inspection of the resource descriptions, rather than relying on their naming convention. The semantics of the description vocabulary is indeed consider more stable across implementations than the naming conventions.



Representations
---------------

Resource representations in kTBS are typically in RDF (except for some `aspect resources`_), either using the standard `RDF/XML`_ syntax, or the alternative Turtle_ syntax. Note also that the N3_ syntax is supported, as it is a superset of Turtle. Support for additional mimetypes can be added to kTBS by using the :mod:`plugin mechanism <ktbs.local.plugins>`.

.. _`RDF/XML`: http://www.w3.org/TR/rdf-primer/
.. _Turtle: http://www.w3.org/2007/02/turtle/primer/
.. _N3: http://www.w3.org/TeamSubmission/n3/

The representations in GET an PUT requests are about existing resources with a known URI. It is therefore quite straightforward to represent those resources in RDF: they appear in the graph as a URI node, and the arcs in the graph represent their relations with other resources and literals. Depending on the type of the represented resources, some `representation constraints` (see below) may apply to the structure of the graph.

.. _posted-graph:
.. _postable-properties:

On the other hand, the representation of a created resource (POST request) deserves more explainations, since their URI is not necessarily known in advance. The POSTed RDF graph must comply with the following rules:

* the target URI of the POST request must be present in the graph as a URI node;
* it must be linked, through exactly one *postable* property (see below), to a
  URI or blank node presenting the to-be-created resource;
* appart from the arc described above, the graph must be a valid description of
  the to-be-created resource (i.e. be compliant with the constraints imposed by
  its type).

The list of *postable* properties, i.e. property which can be used to link a target resource to a newly created resource, is determined by the type of the target resource.

.. admonition:: example

  :doc:`Traces <StoredTrace>` have only one *postable* property: `has_trace`,
  which links theirs obsels (created resources) to themselves.

If the node representing the resource to create is a blank node, kTBS will
make a fresh URI for it. If it is a URI node, kTBS will check that the
URI is not in use, or the creation will fail. In any case, the URI of the newly 
created resource will be provided in the `Location` header field of the
response, as specified by HTTP.

Representation constraints
++++++++++++++++++++++++++

.. _star-shaped:

A common constraint imposed by resource types on the description of their instances is that the graph be *star-shaped*. This implies that:

* every arc in the graph involved the resource being described by the graph;
* the other node in every arc is either a URI or literal node (i.e. no blank
  node).

.. _get-only:
.. _post-only:

Additionnaly, there may be some restrictions on the properties belonging to the
following namespaces, since they have a special meaning for kTBS:

* http://liris.cnrs.fr/silex/2009/rdfrest#
* http://liris.cnrs.fr/silex/2009/ktbs#

Properties from those namespaces may be:

GET-only:
  those properties are automatically generated by kTBS. They are part of the GET
  description, but can not be part of the POSTed description. They may be
  included in the payload of a PUT only if their value is not modified.

POST-only:
  those properties can be initialized at POST time, but after that, they behave
  exactly like GET-only properties.
