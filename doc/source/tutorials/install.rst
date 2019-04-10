Installing and running kTBS
===========================

These tutorials aim at helping you install kTBS and running it, either as a standalone service or behind an HTTP server such as Apache_ or Nginx_.

It has been written using Debian-like systems : `Debian`_ strech and `Ubuntu server`_, but should be applicable with only minor changes (if any) to other flavours of Linux, and a few adaptation on MacOS or MS Windows.

.. toctree::
    :maxdepth: 1
    
    install/install-local-ktbs
    install/install-ktbs-dev-version
    install/install-ktbs-behind-apache
    install/install-ktbs-behind-nginx
    install/install-ktbs-behind-uwsgi
    install/install-ktbs-with-virtuoso

.. _common-prerequisites:

Common Prerequisites
~~~~~~~~~~~~~~~~~~~~

kTBS is a Python_ application, so you need Python installed; more precisely, you need **version 3.6** of Python. kTBS is not compatible anymore with Python 2.

As some dependencies need to be compiled, you will need 
* the `gcc` compiler
* the Python developer files,
* the Berkeley DB developer files.

You can get them with:

.. code-block:: bash

    $ sudo apt-get install python3 gcc python3-dev libdb5.3-dev


.. _Apache: http://httpd.apache.org/
.. _Nginx: http://nginx.org/
.. _Debian: https://www.debian.org/
.. _Ubuntu server: http://www.ubuntu.com/download/server
.. _Python: http://python.org/


