.. _ktbs-rest-tutorial:

kTBS REST Tutorial
==================

This tutorial aims at showing how to create :ref:`kTBS elements <restful-api>` directly in REST_ with Turtle_ configuration files.

.. _REST: http://en.wikipedia.org/wiki/Representational_state_transfer
.. _Turtle: http://www.w3.org/2007/02/turtle/primer/


For the purpose of this tutorial, we will use a local kTBS server. You just have to change the base URI to reach a distant kTBS server.

Tools
-----

We will use **curl** command line tool to communicate with the kTBS server.

Here are the curl options used :

``-i``
    Include the HTTP response headers in the output.

``-X``
    Specify the HTTP request method (defaults to GET) : POST, PUT, DELETE.

``-H``
    Add an HTTP header to the request; used here to specify the content-type.

``--data-binary @filename``
    Set the payload of the HTTP request (PUT or POST) with the content of the given file.

kTBS Root
---------

The kTBS root is automatically created when the kTBS is first launched. Its URI is that of the kTBS server, in our case: ``http://localhost:8001/``.

kTBS Base
---------

Create a new base
^^^^^^^^^^^^^^^^^

You have to POST to the **kTBS root** a simple turtle file describing the **base** to create.

Create a file named ``bas_base1.ttl`` containing the following data:

.. code-block:: turtle

    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    <> :hasBase <base1/>.
    <base1/>
        a :Base ;
        rdfs:label "A trace base" ;
    .

.. note::

  All URIs in that file are relative to the URI of the resource to which we post it; for example, in the file above:

  * ``<>`` will be interpreted as ``<http://localhost:8001/>``,
  * ``<base1/>`` will be interpreted as ``<http://localhost:8001/base1/>``;

  this rule is true for all POST and PUT requests to the kTBS.

Then run the following command: 

.. code-block:: bash

    $ curl http://localhost:8001/ -XPOST -H"Content-type:text/turtle" --data-binary @bas_base1.ttl

It is interesting to use the ``-i`` option to see the HTTP header response. In case of success (``201 Created``), you get the URI of the base in the ``Location`` header, among other HTTP information.

.. code-block:: bash

    $ curl -i http://localhost:8001/ -XPOST -H"Content-type:text/turtle" --data-binary @bas_base1.ttl
    HTTP/1.0 201 Created
    Date: Mon, 10 Oct 2011 15:22:33 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/

KTBS Trace
----------

Create a stored trace
^^^^^^^^^^^^^^^^^^^^^

You have to POST to the **kTBS base** a simple turtle file describing the **stored trace** to create.

Create a file named ``trc_t01.ttl`` containing the following data:

.. code-block:: turtle

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .

    <> :contains <t01/> .

    <t01/>
        a :StoredTrace ;
        :hasModel <http://liris.cnrs.fr/silex/2011/simple-trace-model/> ;
        :hasOrigin "2011-10-13T19:09:00Z"^^xsd:dateTime ;
    .

Then run the following command:

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/ -XPOST -H"Content-type:text/turtle" --data-binary @trc_t01.ttl
    HTTP/1.0 201 Created
    Date: Wed, 12 Oct 2011 17:04:14 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/

Add obsels to trace
^^^^^^^^^^^^^^^^^^^

A first obsel
"""""""""""""

You have to POST to the **kTBS stored trace** a simple turtle file containing describing the **obsel** to create.

Create a file named ``obs1.ttl`` containing the following data:

.. code-block:: turtle

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix ktbs: <http://liris.cnrs.fr/silex/2009/ktbs#> .
    @prefix : <http://liris.cnrs.fr/silex/2011/simple-trace-model#> .

    <obs1> a :SimpleObsel ;
        ktbs:hasBeginDT "2011-10-12T19:15:11.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        ktbs:hasEndDT "2011-10-12T19:15:11.560825"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        ktbs:hasSubject "An interesting  subject";
        ktbs:hasTrace <>;
        :value "My first obsel" .

Then run the following command:

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/t01/ -XPOST -H"Content-type:text/turtle" --data-binary @obs1.ttl
    HTTP/1.0 201 Created
    Date: Wed, 12 Oct 2011 17:22:00 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/obs1

A second obsel linked to the first one
""""""""""""""""""""""""""""""""""""""

Again, you have to POST to the **kTBS stored trace** a simple turtle file describing the second **obsel**.

Create a file named ``obs2.ttl`` containing the following data:

.. code-block:: turtle

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix ktbs: <http://liris.cnrs.fr/silex/2009/ktbs#> .
    @prefix : <http://liris.cnrs.fr/silex/2011/simple-trace-model#> .

    [ a :SimpleObsel ;
        ktbs:hasBeginDT "2011-10-12T19:15:11.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        ktbs:hasEndDT "2011-10-12T19:15:11.560825"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        ktbs:hasSubject "Another interesting  subject";
        ktbs:hasTrace <>;
        :value "My second obsel";
        :hasRelatedObsel <obs1> 
    ].

In this turtle file :

1. We did not specify the URI of this second obsel; instead, we used a blank node; the kTBS will generate a URI for that obsel.
2. We reused the URI of the previous obsel (``<obs1>``) to put a relation between it and the newly created obsel.

Then run the following command:

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/t01/ -XPOST -H"Content-type:text/turtle" --data-binary @obs2.ttl
    HTTP/1.0 201 Created
    Date: Wed, 12 Oct 2011 17:53:52 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/6e59cd1841cfba471e26933c84e31ed4

We can retrieve the URI generated by the kTBS for the new obsel in the ``Location`` header of the HTTP response.
