.. _ktbs-rest-tutorial:

kTBS REST Tutorial
==================

This tutorial aims at showing how to create :ref:`kTBS elements <restful-api>` directly in REST_ with Turtle_ configuration files.

.. _REST: http://en.wikipedia.org/wiki/Representational_state_transfer
.. _Turtle: http://www.w3.org/2007/02/turtle/primer/


For the purpose of this tutorial, we will use a local kTBS server. You just have to change the base URI to reach a distant kTBS server.

Tools
-----

curl
^^^^

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

browser
^^^^^^^

You can navigate in the kTBS content with any browser, from the kTBS root ``http://localhost:8001/``.

Create and populate a Stored Trace
----------------------------------

kTBS Root
^^^^^^^^^

The kTBS root is automatically created when the kTBS is first launched. Its URI is that of the kTBS server, in our case: ``http://localhost:8001/``.

kTBS Base
^^^^^^^^^

Create a new base
"""""""""""""""""

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
    Date: Tue, 29 Nov 2011 09:41:06 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/

KTBS Trace
^^^^^^^^^^

Create a stored trace
"""""""""""""""""""""

You have to POST to the **kTBS base** a simple turtle file describing the **stored trace** to create.

Create a file named ``trc_t01.ttl`` containing the following data:

.. code-block:: turtle

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .

    <> :contains <t01/> .

    <t01/>
        a :StoredTrace ;
        :hasModel <http://liris.cnrs.fr/silex/2011/simple-trace-model/> ;
        :hasOrigin "2011-10-13T19:00:00Z"^^xsd:dateTime ;
    .

Then run the following command:

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/ -XPOST -H"Content-type:text/turtle" --data-binary @trc_t01.ttl
    HTTP/1.0 201 Created
    Date: Tue, 29 Nov 2011 09:41:06 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/

Add obsels to trace
"""""""""""""""""""

**A first obsel**

You have to POST to the **kTBS stored trace** a simple turtle file containing describing the **obsel** to create.

Create a file named ``obs1.ttl`` containing the following data:

.. code-block:: turtle

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix ktbs: <http://liris.cnrs.fr/silex/2009/ktbs#> .
    @prefix : <http://liris.cnrs.fr/silex/2011/simple-trace-model#> .

    <obs1> a :SimpleObsel ;
        ktbs:hasBeginDT "2011-10-13T19:01:01.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        ktbs:hasEndDT "2011-10-13T19:01:01.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        ktbs:hasSubject "An interesting  subject";
        ktbs:hasTrace <>;
        :value "My first obsel" .

Then run the following command:

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/t01/ -XPOST -H"Content-type:text/turtle" --data-binary @obs1.ttl
    HTTP/1.0 201 Created
    Date: Tue, 29 Nov 2011 09:41:06 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/obs1

**A second obsel linked to the first one**

Again, you have to POST to the **kTBS stored trace** a simple turtle file describing the second **obsel**.

Create a file named ``obs2.ttl`` containing the following data:

.. code-block:: turtle

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix ktbs: <http://liris.cnrs.fr/silex/2009/ktbs#> .
    @prefix : <http://liris.cnrs.fr/silex/2011/simple-trace-model#> .

    [ a :SimpleObsel ;
        ktbs:hasBeginDT "2011-10-13T19:01:02.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        ktbs:hasEndDT "2011-10-13T19:01:02.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
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
    Date: Tue, 29 Nov 2011 09:41:06 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/t01/6e59cd1841cfba471e26933c84e31ed4

We can retrieve the URI generated by the kTBS for the new obsel in the ``Location`` header of the HTTP response.

Create a Computed Trace
-----------------------

The kTBS has a number of :doc:`builtin methods <../concepts/method>` to create Computed Traces.

Here are the obsels of the Stored Trace we have just created:

.. code-block:: turtle

    $ curl -i http://localhost:8001/base1/t01/@obsels
    HTTP/1.0 200 OK
    Date: Tue, 29 Nov 2011 11:07:11 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    ETag: "bddc3537fac130224891bb42c2dab1b1"
    Content-Type: text/turtle
    Content-Length: 1603
    Content-Location: http://localhost:8001/base1/t01/@obsels.ttl
    Vary: Accept
    Cache-control: max-age=0


    @prefix _7: <http://localhost:8001/base1/t01/>.
    @prefix _8: <http://liris.cnrs.fr/silex/2011/simple-trace-model#>.
    @prefix _9: <http://localhost:8001/base1/t01/62>.
    @prefix ktbs: <http://liris.cnrs.fr/silex/2009/ktbs#>.
    @prefix owl: <http://www.w3.org/2002/07/owl#>.
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
    @prefix rdfrest: <http://liris.cnrs.fr/silex/2009/rdfrest#>.
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
    @prefix xml: <http://www.w3.org/XML/1998/namespace>.
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

     _9:bb48cc5d01f4671e46933caa9797eb a _8:SimpleObsel;
         ktbs:hasBegin "62551"^^<http://www.w3.org/2001/XMLSchema#integer>;
         ktbs:hasBeginDT "2011-10-13T19:01:02.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
         ktbs:hasEnd "62551"^^<http://www.w3.org/2001/XMLSchema#integer>;
         ktbs:hasEndDT "2011-10-13T19:01:02.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
         ktbs:hasSubject "Another interesting  subject";
         ktbs:hasTrace <http://localhost:8001/base1/t01/>;
         _8:hasRelatedObsel _7:obs1;
         _8:value "My second obsel". 

     _7:obs1 a _8:SimpleObsel;
         ktbs:hasBegin "61551"^^<http://www.w3.org/2001/XMLSchema#integer>;
         ktbs:hasBeginDT "2011-10-13T19:01:01.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
         ktbs:hasEnd "61551"^^<http://www.w3.org/2001/XMLSchema#integer>;
         ktbs:hasEndDT "2011-10-13T19:01:01.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
         ktbs:hasSubject "An interesting  subject";
         ktbs:hasTrace <http://localhost:8001/base1/t01/>;
         _8:value "My first obsel". (ktbs-3.0)# fconil@liristus (origin:master * u=) ~/PyEnvs27/ktbs-3.0

Create a Computed Trace with a filter method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You have to POST to the kTBS base a simple turtle file describing the computed trace to create.

Create a file named ``trc_filter1.ttl`` containing the following data:

.. code-block:: turtle

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .

    <> :contains <filteredTrace1/> .

    <filteredTrace1/>
        a :ComputedTrace ;
        :hasMethod :filter ;
        :hasSource <t01/> ;
        :hasParameter "finish=62000" ;
    .

This create a computed trace named ``filteredTrace1`` based on a *temporal filters* which copies into ``filteredTrace1`` the ``t01`` obsels whose ``hasBegin`` property is lower than 62000 (ms).

.. note::

    The ``hasBegin`` and ``hasEnd`` properties are integers values either filled or computed by the kTBS.

    * ``hasBegin`` is the number of milliseconds between the trace ``hasOrigin`` property and the obsel ``hasBeginDT``.
    * ``hasEnd`` is the number of milliseconds between the trace ``hasOrigin`` property and the obsel ``hasEndDT``.

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/ -XPOST -H"Content-type:text/turtle" --data-binary @trc_filtered1.ttl
    HTTP/1.0 201 Created
    Date: Tue, 29 Nov 2011 11:51:35 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/filteredTrace1/


Create a Computed Trace with a SPARQL query
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You have to POST to the kTBS base a simple turtle file describing the computed trace to create.

Create a file named ``trc_sparql1.ttl`` containing the following data:

.. code-block:: turtle

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .

    <> :contains <FindSecondText/> .

    <FindSecondText/>
        a :ComputedTrace ;
        :hasMethod :sparql ;
        :hasSource <t01/> ;
        :hasParameter """sparql=
    PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>
    PREFIX :  <http://liris.cnrs.fr/silex/2011/simple-trace-model#>

    CONSTRUCT {
        [ a :SimpleObsel ;
          k:hasTrace <%(__destination__)s> ;
          k:hasBegin ?begin ;
          k:hasBeginDT ?begindt ;
          k:hasEnd ?end ;
          k:hasEndDT ?enddt ;
          k:hasSourceObsel ?obsel ;
          :value ?value ;
        ] .
    } WHERE {
        ?obsel a :SimpleObsel ;
          k:hasBegin ?begin ;
          k:hasBeginDT ?begindt ;
          k:hasEnd ?end ;
          k:hasEndDT ?enddt ;
          :value ?value ;
          FILTER regex(?value, "second", "i") .
    }
    """ ;
    .

This create a computed trace named ``FindSecondText`` based on a SPARQL construct query which creates ``FindSecondText`` with the ``t01`` obsels whose ``value`` property contains the ``second`` text.

.. note::

    The computed trace created with SPARQL construct can use a different model than the source trace. Look at ``Sparql rule`` builtin method documentation.

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/ -XPOST -H"Content-type:text/turtle" --data-binary @trc_sparql1.ttl
    HTTP/1.0 201 Created
    Date: Tue, 29 Nov 2011 12:18:15 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/FindSecondText/

Create a Computed Trace with a fusion method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You have to POST to the kTBS base a simple turtle file describing the computed trace to create.

Create a file named ``trc_fusioned1.ttl`` containing the following data:

.. code-block:: turtle

    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .
    <> :contains <fusionedTrace1/> .

    <fusionedTrace1/>
        a :ComputedTrace ;
        :hasMethod :fusion ;
        :hasSource <FindSecondText/>, <filteredTrace1/> ;
    .

This creates a computed trace named ``fusionedTrace1`` which is a merge of the ``FindSecondText`` and the ``filteredTrace1`` traces.

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/ -XPOST -H"Content-type:text/turtle" --data-binary @trc_fusioned1.ttl
    HTTP/1.0 201 Created
    Date: Tue, 29 Nov 2011 12:34:35 GMT
    Server: WSGIServer/0.1 Python/2.6.7
    Content-Type: text/plain
    Content-Length: 
    Location: http://localhost:8001/base1/fusionedTrace1/

