.. _ktbs-rest-tutorial:

kTBS REST Tutorial
==================

This tutorial aims at showing how to create kTBS elements [1]_ directly in REST [2]_ with Turtle [3]_ configuration files.

For the purpose of this tutorial, we will use a local kTBS server. You just have to change the base URI to reach a distant kTBS server.

Tools
-----

We will use **curl** command line tool to communicate with the kTBS server.

curl options used :

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

::

    $ curl http://localhost:8001/ -XPOST -H"Content-type:text/turtle" --data-binary @bas_base1.ttl

You POST to the **kTBS root** a simple turtle file containing **base** information. 

It is interesting to use ``-i`` option to get the HTTP header response. In case of success (201 Created), you get the base url in the ``Location`` header and other HTTP information.

::

    $ curl -i http://localhost:8001/ -XPOST -H"Content-type:text/turtle" --data-binary @bas_base1.ttl
    HTTP/1.0 201 Created
    Date: Mon, 10 Oct 2011 15:22:33 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/

Where the turtle base configuration is the following :

::

    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    <> :hasBase <base1/>.
    <base1/>
        a :Base ;
        rdfs:label "A trace base" ;
    .

.. [1] :ref:`restful-api`
.. [2] http://en.wikipedia.org/wiki/Representational_state_transfer
.. [3] http://www.w3.org/2007/02/turtle/primer/

KTBS Trace
----------

Create a stored trace
^^^^^^^^^^^^^^^^^^^^^

::

    $ curl -i http://localhost:8001/base1/ -XPOST -H"Content-type:text/turtle" --data-binary @trc_t01.ttl
    HTTP/1.0 201 Created
    Date: Wed, 12 Oct 2011 17:04:14 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/

You POST to the **kTBS base** a turtle file containing the **stored trace** information. Here is the turtle file used :

::

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .

    <> :contains <t01/> .

    <t01/>
        a :StoredTrace ;
        :hasModel <http://liris.cnrs.fr/silex/2011/simple-trace-model/> ;
        :hasOrigin "2011-10-13T19:09:00Z"^^xsd:dateTime ;
    .

Add obsels to trace
^^^^^^^^^^^^^^^^^^^

A first obsel
"""""""""""""

::

    $ curl -i http://localhost:8001/base1/t01/ -XPOST -H"Content-type:text/turtle" --data-binary @obs1.ttl
    HTTP/1.0 201 Created
    Date: Wed, 12 Oct 2011 17:22:00 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/obs1

You POST to the **kTBS stored trace** a turtle file containing the **obsel** information. Here is the turtle file used :

::

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix ktbs: <http://liris.cnrs.fr/silex/2009/ktbs#> .
    @prefix : <http://liris.cnrs.fr/silex/2011/simple-trace-model#> .

    <obs1> a :SimpleObsel ;
        ktbs:hasBeginDT "2011-10-12T19:15:11.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        ktbs:hasEndDT "2011-10-12T19:15:11.560825"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        ktbs:hasSubject "An interesting  subject";
        ktbs:hasTrace <>;
        :value "My first obsel" .

A second obsel linked to the first
""""""""""""""""""""""""""""""""""

We now create a second obsel, which we do not fix the uri and that will be linked to the firts obsel created.

::

    $ curl -i http://localhost:8001/base1/t01/ -XPOST -H"Content-type:text/turtle" --data-binary @obs2.ttl
    HTTP/1.0 201 Created
    Date: Wed, 12 Oct 2011 17:53:52 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/6e59cd1841cfba471e26933c84e31ed4

Here we have the turtle file containing the **obsel** information did not specify the obsel URI so a blank node has been generated. Here is the turtle file used :

::

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
