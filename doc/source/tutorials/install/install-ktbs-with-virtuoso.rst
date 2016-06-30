Installing kTBS with a Virtuoso backend
=======================================

kTBS will typically use its own triple-store,
which is good for small to medium traces,
but does not scale well to big traces (10k obsels or more).

For bigger traces,
it is possible to use `Virtuoso <http://virtuoso.openlinksw.com/>`_,
a state-of-the-art triple store supporting high volumes of data.

Here are the steps necessary to do so:

* You need to setup a Virtuoso server;
  you can for example use the Docker image provided at https://hub.docker.com/r/joernhees/virtuoso/,
  and ensure that both ports 8890 and 1111 are accessible to kTBS.

* You need the client ODBC library for accessing Virtuoso,
  as well as development files for ODBC and Python.
  On Debian/Ubuntu Linux, you can get it with::

    apt-get install libvirtodbc0 unixodbc-dev python2.7-dev

* Add the following lines in ``~/.odbc.ini`` or ``/etc/odbc.ini``::

    [VOS]
    Description = Open Virtuoso
    Driver      = /usr/lib/odbc/virtodbcu_r.so
    Address     = localhost:1111
    Locale      = en.UTF-8

* You need a customized version of the ``pyodbc`` module,
  available at https://github.com/maparent/pyodbc,
  in the branch ``v3-virtuoso``.

  One way to achieve that is the following::

    pip install git+https://github.com/maparent/pyodbc@v3-virtuoso

* Finally, you need the ``virtuoso-python`` module,
  available at https://github.com/pchampin/virtuoso-python,
  in the branch ``rdflib_improvements``.

  One way to achieve that is the following::

    pip install git+https://github.com/pchampin/virtuoso-python@rdflib_improvements

* Finally,
  all you need to do is to configure the RDF store used by kTBS to::

    :Virtuoso:DSN=VOS;UID=dba;PWD=dba;WideAsUTF16=Y

.. important::

   On the first run, you need the ``--force-init`` option to force kTBS to initalize the RDF store.

.. warning::

   The ``virtuoso-python`` library does not allow several threads of the same process to process queries in parallel,
   so if you kTBS to do so, you will need to configure it to use distinct *processes* rather than threads
   (for example in ``wsgi_mod`` `configuration <install-ktbs-behind-apache>`:doc:).
