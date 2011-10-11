.. _ktbs-rest-tutorial:

KTBS REST Tutorial
==================

This tutorial aims at showing how to create KTBS elements directly in REST [1]_ with Turtle configuration files.

For the purpose of this tutorial, we will use a local KTBS server. You just have to change the base URI to reach a distant KTBS server.

Tools
-----

We will use **curl** command line tool to communicate with the KTBS server.

curl options used :

``-i``
    Include the HTTP-header in the output.

``-X``
    Specify the HTTP request method (defaults to GET) : POST, PUT, DELETE.

``--data-binary @filename``
    This posts data exactly as specified with no extra processing whatsoever. The data is supposed to be contained in the file identified by ``filename``.

KTBS Root
---------
When a KTBS server is launched, it has a default KTBS Root.

The URI of our local KTBS server is ``http://localhost:8001/``.

KTBS Base
---------

Create a new base
^^^^^^^^^^^^^^^^^


::

    $ curl -i http://localhost:8001/ -XPOST "Content-type:text/turtle" --data-binary @bas_base1.ttl
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

.. [1] http://en.wikipedia.org/wiki/Representational_state_transfer
