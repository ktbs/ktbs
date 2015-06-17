Installing and running kTBS
===========================

These tutorials aim at helping you install kTBS and running it, either as a standalone service or behind an HTTP server such as Apache_ or nginx_.

It has been written using Debian like systems : Debian wheezy (> 7.n) and `Ubuntu server`_ (from 12.10 to 14.10), but should be applicable with only minor changes (if any) to other flavours of Linux, and a few adaptation on MacOS or MS Windows [#]_.

.. toctree::
    :maxdepth: 1 
    
    install/install-local-ktbs
    install/install-ktbs-dev-version
    install/install-ktbs-behind-apache
    install/install-ktbs-behind-nginx

.. _common-prerequisites:

Common Prerequisites
~~~~~~~~~~~~~~~~~~~~

kTBS is a Python_ application, so you need Python installed; more precisely, you need **version 2.7** of Python. kTBS is not compatible with older version, nor with the newer Python 3. Python 2.7 will typically be already pre-installed on your Linux distribution.

As some dependencies need to be compiled, you also need python developer files. You can get them with

.. code-block:: bash

    $ sudo apt-get install python-dev

We also advise you to use virtualenv_, this tool creates an isolated Python environment, so that kTBS and its dependencies can be installed without interference with Python packages installed in your system. To install virtualenv_, type

.. code-block:: bash

    $ sudo apt-get install python-virtualenv 

.. rubric:: Notes

.. [#] a tutorial for installing Python and Virtualenv on Windows is available
       at http://www.tylerbutler.com/2012/05/how-to-install-python-pip-and-virtualenv-on-windows-with-powershell/

.. [#] the protocol, server name and port number depend on the enclosing ``VirtualHost`` directive


.. _Apache: http://httpd.apache.org/
.. _nginx: http://nginx.org/
.. _Ubuntu server: http://www.ubuntu.com/download/server
.. _Python: http://python.org/
.. _virtualenv: http://www.virtualenv.org/

