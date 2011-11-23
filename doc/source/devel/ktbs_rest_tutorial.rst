.. _ktbs-rest-tutorial:

kTBS REST Tutorial
==================

This tutorial aims at showing how to create kTBS elements [1]_ directly in REST [2]_ with Turtle configuration files [3]_.

For the purpose of this tutorial, we will use a local kTBS server. You just have to change the base URI to reach a distant kTBS server.

Tools
-----

We will use **curl** command line tool to communicate with the kTBS server.

Here are the curl options used :

``-i``
    Include the HTTP-header in the output.

``-X``
    Specify the HTTP request method (defaults to GET) : POST, PUT, DELETE.

``--data-binary @filename``
    This posts data exactly as specified with no extra processing whatsoever. The data is supposed to be contained in the file identified by ``filename``.

kTBS Root
---------
When a kTBS server is launched, it has a default kTBS Root.

The URI of our local kTBS server is ``http://localhost:8001/``.

kTBS Base
---------

Create a new base
^^^^^^^^^^^^^^^^^

You have to POST to the **kTBS root** a simple turtle file containing **base** information. 

Create a file named ``bas_base1.ttl`` containing the following data:

.. code-block:: turtle

    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    <> :hasBase <base1/>.
    <base1/>
        a :Base ;
        rdfs:label "A trace base" ;
    .

Then run the following command: 

.. code-block:: bash

    $ curl http://localhost:8001/ -XPOST -H"Content-type:text/turtle" --data-binary @bas_base1.ttl

It is interesting to use ``-i`` option to get the HTTP header response. In case of success (201 Created), you get the base url in the ``Location`` header and other HTTP information.

.. code-block:: bash

    $ curl -i http://localhost:8001/ -XPOST -H"Content-type:text/turtle" --data-binary @bas_base1.ttl
    HTTP/1.0 201 Created
    Date: Mon, 10 Oct 2011 15:22:33 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/

.. [1] :ref:`restful-api`
.. [2] http://en.wikipedia.org/wiki/Representational_state_transfer
.. [3] http://www.w3.org/2007/02/turtle/primer/

KTBS Trace
----------

Create a stored trace
^^^^^^^^^^^^^^^^^^^^^

You have to POST to the **kTBS base** a simple turtle file containing **stored trace** information.

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

You have to POST to the **kTBS stored trace** a simple turtle file containing **obsel** information.

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

A second obsel linked to the first
""""""""""""""""""""""""""""""""""

You have to POST to the **kTBS stored trace** a simple turtle file containing the second **obsel** information.

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

1. We did not specify the URI of this second obsel so a blank node will been generated.
2. We do not fix the uri and that will be linked to the firts obsel created.

Then run the following command:

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/t01/ -XPOST -H"Content-type:text/turtle" --data-binary @obs2.ttl
    HTTP/1.0 201 Created
    Date: Wed, 12 Oct 2011 17:53:52 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/6e59cd1841cfba471e26933c84e31ed4
