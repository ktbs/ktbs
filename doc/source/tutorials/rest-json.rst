.. _ktbs-rest-jsonld-tutorial:

Using kTBS with REST and JSON
=============================

This tutorial aims at showing how to create :ref:`kTBS elements <restful-api>` directly through the REST_ API with JSON_ descriptions.

.. note:: The JSON syntax used in kTBS complies with JSON-LD_ in order to accurately represent the underlying RDF_ model.

.. _REST: http://en.wikipedia.org/wiki/Representational_state_transfer
.. _JSON: http://www.json.org/
.. _RDF: http://www.w3.org/RDF/
.. _JSON-LD: http://json-ld.org/

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

You have to POST to the **kTBS root** a simple json file describing the **base** to create.

Create a file named ``bas_base1.jsonld`` containing the following data:

.. code-block:: javascript

    {
        "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
        "@id": "base1/",
        "@type": "Base",
        "label": "A trace base"
    }

.. note::

  All URIs in that file are relative to the URI of the resource to which we post it; for example, in the file above:

  * ``""`` will be interpreted as ``http://localhost:8001/``,
  * ``base1/`` will be interpreted as ``http://localhost:8001/base1/``;

  this rule is true for all POST and PUT requests to the kTBS.

Then run the following command: 

.. code-block:: bash

    $ curl http://localhost:8001/ -XPOST -H"Content-type:application/json" --data-binary @bas_base1.jsonld


It is interesting to use the ``-i`` option to see the HTTP header response. In case of success (``201 Created``), you get the URI of the base in the ``Location`` header, among other HTTP information.

.. code-block:: bash

    $ curl -i http://localhost:8001/ -XPOST -H"Content-type:application/json" --data-binary @bas_base1.jsonld
    HTTP/1.0 201 Created
    Date: Tue, 31 Jan 2012 09:20:07 GMT
    Server: WSGIServer/0.1 Python/2.7.2
    location: http://localhost:8001/base1/
    Content-Length: 28

KTBS Trace
^^^^^^^^^^

Create a stored trace
"""""""""""""""""""""

You have to POST to the **kTBS base** a simple json file describing the **stored trace** to create.

Create a file named ``trc_t01.jsonld`` containing the following data:

.. code-block:: javascript

    {
        "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
        "@id": "t01/",
        "@type": "StoredTrace",
        "hasModel": "http://liris.cnrs.fr/silex/2011/simple-trace-model/",
        "origin": "2011-10-13T19:00:00Z"
    }

Then run the following command:

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/ -XPOST -H"Content-type:application/json" --data-binary @trc_t01.jsonld
    HTTP/1.0 201 Created
    Date: Tue, 31 Jan 2012 10:36:19 GMT
    Server: WSGIServer/0.1 Python/2.7.2
    location: http://localhost:8001/base1/t01/
    Content-Length: 32

Add obsels to trace
"""""""""""""""""""

**A first obsel**

You have to POST to the **kTBS stored trace** a simple json file containing describing the **obsel** to create.

Create a file named ``obs1.jsonld`` containing the following data:

.. code-block:: javascript

    {
        "@context": [
                        "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
                        { "m": "http://liris.cnrs.fr/silex/2011/simple-trace-model#" }
                    ],
        "@id": "obs1",
        "@type": "m:SimpleObsel",
        "hasTrace": "",
        "beginDT": "2011-10-13T19:01:01.551529",
        "endDT": "2011-10-13T19:01:01.551529",
        "subject": "An interesting  subject",
        "m:value": "My first obsel"
    }

Then run the following command:

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/t01/ -XPOST -H"Content-type:application/json" --data-binary @obs1.jsonld
    HTTP/1.0 201 Created
    Date: Wed, 01 Feb 2012 13:44:27 GMT
    Server: WSGIServer/0.1 Python/2.7.2
    location: http://localhost:8001/base1/t01/obs1
    Content-Length: 36

**A second obsel linked to the first one**

Again, you have to POST to the **kTBS stored trace** a simple json file describing the second **obsel**.

Create a file named ``obs2.jsonld`` containing the following data:


.. code-block:: javascript

    {
        "@context": [
                        "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
                        {
                            "m": "http://liris.cnrs.fr/silex/2011/simple-trace-model#",
                            "m:hasRelatedObsel":
                            {
                                "@type": "@id"
                            }
                        }
                    ],
        "@type": "m:SimpleObsel",
        "hasTrace": "",
        "beginDT": "2011-10-13T19:01:01.551529",
        "endDT": "2011-10-13T19:01:01.551529",
        "subject": "Another interesting  subject",
        "m:value": "My second obsel",
        "m:hasRelatedObsel": "obs1"
    }


In this json file :

1. We did not specify the URI of this second obsel; instead, we used a blank node; the kTBS will generate a URI for that obsel.
2. We reused the URI of the previous obsel (``"obs1"``) to put a relation between it and the newly created obsel.

Then run the following command:

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/t01/ -XPOST -H"Content-type:application/json" --data-binary @obs2.jsonld
    HTTP/1.0 201 Created
    Date: Wed, 01 Feb 2012 16:52:56 GMT
    Server: WSGIServer/0.1 Python/2.7.2
    location: http://localhost:8001/base1/t01/obsel
    Content-Length: 37

We can retrieve the URI generated by the kTBS for the new obsel in the ``Location`` header of the HTTP response. **But the blank node does not seem to have a good generated URI**

Create a Computed Trace
-----------------------

The kTBS has a number of :doc:`builtin methods <../concepts/method>` to create Computed Traces.

Here are the obsels of the Stored Trace we have just created:

.. code-block:: turtle

    $ curl -i http://localhost:8001/base1/t01/@obsels
    HTTP/1.0 200 OK
    Date: Wed, 01 Feb 2012 17:05:31 GMT
    Server: WSGIServer/0.1 Python/2.7.2
    content-type: text/turtle
    content-location: http://localhost:8001/base1/t01/@obsels.ttl
    etag: W/"text/turtle/00311500a0f137c8774414cbf95e4257"
    last-modified: 2012-02-01T18:00:22.650000

    @prefix : <http://liris.cnrs.fr/silex/2009/ktbs#> .
    @prefix ns1: <http://liris.cnrs.fr/silex/2011/simple-trace-model#> .

    <http://localhost:8001/base1/t01/obsel> a <http://liris.cnrs.fr/silex/2011/simple-trace-model#SimpleObsel>;
        :hasBegin 61551;
        :hasBeginDT "2011-10-13T19:01:01.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        :hasEnd 61551;
        :hasEndDT "2011-10-13T19:01:01.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        :hasSubject "Another interesting  subject";
        :hasTrace <http://localhost:8001/base1/t01/>;
        ns1:hasRelatedObsel <http://localhost:8001/base1/t01/obs1>;
        ns1:value "My second obsel" .

    <http://localhost:8001/base1/t01/obs1> a <http://liris.cnrs.fr/silex/2011/simple-trace-model#SimpleObsel>;
        :hasBegin 61551;
        :hasBeginDT "2011-10-13T19:01:01.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        :hasEnd 61551;
        :hasEndDT "2011-10-13T19:01:01.551529"^^<http://www.w3.org/2001/XMLSchema#dateTime>;
        :hasSubject "An interesting  subject";
        :hasTrace <http://localhost:8001/base1/t01/>;
        ns1:value "My first obsel" .

Create a Computed Trace with a filter method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You have to POST to the kTBS base a simple json file describing the computed trace to create.

Create a file named ``trc_filter1.jsonld`` containing the following data:

.. code-block:: javascript

    {
        "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
        "@id": "filteredTrace1/",
        "@type": "ComputedTrace",
        "hasMethod": "filter",
        "hasSource": "t01",
        "parameter": "finish=62000"
    }

This create a computed trace named ``filteredTrace1`` based on a *temporal filters* which copies into ``filteredTrace1`` the ``t01`` obsels whose ``hasBegin`` property is lower than 62000 (ms).

.. note::

    The ``hasBegin`` and ``hasEnd`` properties are integers values either filled or computed by the kTBS.

    * ``hasBegin`` is the number of milliseconds between the trace ``hasOrigin`` property and the obsel ``hasBeginDT``.
    * ``hasEnd`` is the number of milliseconds between the trace ``hasOrigin`` property and the obsel ``hasEndDT``.

.. code-block:: bash

    $ curl -i http://localhost:8001/base1/ -XPOST -H"Content-type:application/json" --data-binary @trc_filtered1.jsonld
    HTTP/1.0 500 Internal Server Error
    Date: Wed, 01 Feb 2012 17:27:29 GMT
    Server: WSGIServer/0.1 Python/2.7.2
    Content-Type: text/plain
    Content-Length: 59

Here is the turtle serialized from the graph generated with the json data sent.

.. code-block:: turtle

    @prefix ns1: <http://liris.cnrs.fr/silex/2009/ktbs#> .

    <http://localhost:8001/base1/> ns1:contains <http://localhost:8001/base1/filteredTrace1/> .

    <http://localhost:8001/base1/filteredTrace1/> a <http://liris.cnrs.fr/silex/2009/ktbs#ComputedTrace>;
        ns1:hasMethod <http://liris.cnrs.fr/silex/2009/ktbs#filter>;
        ns1:hasParameter "finish=62000";
        ns1:hasSource <http://localhost:8001/base1/t01> .

