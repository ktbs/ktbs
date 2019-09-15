Installing and running kTBS
===========================

These tutorials aim at helping you install kTBS and running it, either as a standalone service or behind an HTTP server such as Apache_ or Nginx_.

It has been written using Debian-like systems : `Debian`_ strech and `Ubuntu server`_, but should be applicable with only minor changes (if any) to other flavours of Linux, and a few adaptation on MacOS or MS Windows.

.. toctree::
    :maxdepth: 1
    
    install/install-local-ktbs
    install/install-ktbs-behind-apache
    install/install-ktbs-behind-nginx

.. _common-prerequisites:

Common Prerequisites
++++++++++++++++++++

Dependencies
~~~~~~~~~~~~

kTBS is a Python_ application, so you need Python installed; more precisely, you need **version 3.7** of Python. kTBS is not compatible anymore with Python 2.

As some dependencies need to be compiled, you will need

* the ``gcc`` compiler
* the Python developer files,
* the Berkeley DB developer files.

If you intend to install kTBS from the source (which is the recommended way), you will also need ``git``.

On a Debian or Ubuntu, you should be able to get these dependencies by typing:

.. code-block:: bash

    $ sudo apt-get install python3 gcc python3-dev libdb5.3-dev git

Create the Python vitual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A Python `virtual environment`__ creates an isolated version of Python,
where you can install a Python application (such as kTBS)
and all its dependencies without "polluting" your operating system.
Conversely, the Python libraries already installed in your system do not interfere with the virtual environment.

__ https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments

Let us create a virtual environment for kTBS.

.. code-block:: bash

    $ python3 -m venv ktbs-env

This will create a directory named ``ktbs-env`` (but you can choose another name, it makes no difference to kTBS).

.. _activate-venv:

The virtual environnement is then activated by **sourcing** the ``activate`` script. Once it is done, you can notice that

* the prompt has changed to remind you that the virtual environment is active, and
* the default Python interpreter is the one from the virtual environment.

.. code-block:: bash

    $ source ktbs-env/bin/activate

    (ktbs-env) $ which python
    /current-dir/ktbs-env/bin/python

You "leave" the virtual environment by running the ``deactivate`` command.

.. code-block:: bash

    (ktbs-env) $ deactivate

    $ which python
    /usr/bin/python

.. _Apache: http://httpd.apache.org/
.. _Nginx: http://nginx.org/
.. _Debian: https://www.debian.org/
.. _Ubuntu server: http://www.ubuntu.com/download/server
.. _Python: http://python.org/
