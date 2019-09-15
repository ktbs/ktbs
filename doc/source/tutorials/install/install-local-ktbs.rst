Installing a local kTBS
=======================

Make sure you have read and executed the :ref:`common-prerequisites` instructions, i.e installed all dependencies, and a Python virtual environment.

.. _create-python-virtual_env:

Installing  the development version (recommended)
+++++++++++++++++++++++++++++++++++++++++++++++++

Ensure that you have `activated your virtual environment <activate-venv>`:ref:.
Get the source code and install it in your virtual environment with `pip -e`.

.. code-block:: bash
    :emphasize-lines: 1,10

    (ktbs-env) $ git clone https://github.com/ktbs/ktbs.git
    Cloning into 'ktbs'...
    remote: Enumerating objects: 53, done.
    remote: Counting objects: 100% (53/53), done.
    remote: Compressing objects: 100% (36/36), done.
    remote: Total 6842 (delta 17), reused 37 (delta 15), pack-reused 6789
    Receiving objects: 100% (6842/6842), 2.72 MiB | 1.11 MiB/s, done.
    Resolving deltas: 100% (4400/4400), done.

    (ktbs-env) $ pip install -e ktbs/

.. note::

    The ``-e`` option makes pip install the current project in editable mode.
    It means that whenever you update the repository with ``git pull``, of if you edit the code, the changes will be taken into account automatically.

If you intend to contribute, you might also want to install the developer's dependencies:

.. code-block:: bash

    (ktbs-env) $ pip install -r ktbs/requirements.d/dev.txt

Installing the stable version
+++++++++++++++++++++++++++++

**Instead** of installing kTBS from the source code,
you can install it and its dependencies from `PyPI <https://pypi.python.org/pypi>`_.
Ensure that you have `activated your virtual environment <activate-venv>`:ref:,
and simply type:

.. code-block:: bash

    (ktbs-env) $ pip install ktbs


Note however that the stable version is not updated very often,
and so might very quickly be outdated compared to the development version.
Hence, this option is **not recommended**.

Testing the installed kTBS
++++++++++++++++++++++++++

Once installed, just run the **ktbs** command, it launches an internal HTTP server on the 8001 port (by default).

.. code-block:: bash

    (ktbs-env) $ ktbs
    INFO	2019-09-15 14:28:18 CEST	ktbs.server	PID: 26566
    INFO	2019-09-15 14:28:18 CEST	ktbs.server	listening on http://localhost:8001/

You stop kTBS with ``Ctrl-C``.

Make the trace bases persistent
+++++++++++++++++++++++++++++++

By default, kTBS stores the trace bases in memory, so they will not be retained after you stop kTBS.  To make the trace bases persistent, you need to **configure a repository**. 

This can be done with the ``-r`` option.

.. code-block:: bash

    (ktbs-env) $ ktbs -r <dirname>

A directory named ``<dirname>`` will be used to store the trace bases; if it does not exist, it will be automatically created and initialized.

.. note::

  You must *not* create the directory for the store; if the directory already exists, kTBS will assume that it is correctly initialized, and fail if it is not the case (*e.g.* if it is empty).


.. _ktbs-configuration-file:

Advanced configuration
++++++++++++++++++++++

There are a lot more configuration options that you can set on the command lines
(type ``ktbs --help`` for a list).
But a safer way to configure your kTBS instance is to store those options in a configuration file.
An example is provided in the `example/conf/`__ directory of the source code.
Then, pass the configuration file as an argument to kTBS:

.. code-block:: bash

    (ktbs-env) $ ktbs my.conf
    INFO	2019-09-15 14:28:18 CEST	ktbs.server	PID: 26567
    INFO	2019-09-15 14:28:18 CEST	ktbs.server	listening on http://localhost:1234/

__ https://github.com/ktbs/ktbs/tree/develop/examples/conf/
