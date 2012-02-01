.. _ktbs-rest-jsonld-tutorial:

kTBS REST JSON-LD Tutorial
==========================

This tutorial aims at showing how to create :ref:`kTBS elements <restful-api>` directly in REST_ with JSON-LD_ configuration files.

.. _REST: http://en.wikipedia.org/wiki/Representational_state_transfer
.. _JSON-LD: http://json-ld.org/spec/latest/json-ld-syntax/ 


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

