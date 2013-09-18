Installing and running kTBS
===========================

This tutorial aims at helping you install kTBS and running it,
either as a standalone service or behind an Apache_ HTTP server.
It has been written using `Ubuntu server`_ 12.10,
but should be applicable
with only minor changes (if any) to other flavours of Linux,
and a few adaptation on MacOS or MS Windows [#]_.


Installing kTBS
+++++++++++++++

kTBS is a Python_ application, so you need python installed; more precisely, you need **version 2.7** of Python. kTBS is not compatible with older version, nor with the newer Python 3. Python 2.7 will typically be already pre-installed on your Linux distribution.

We also advise you to use Virtualenv_; this tool creates an autonomous environment for Python programs, so that kTBS and its dependencies can be installed without interference with Python packages installed in your system. To install Virtualenv, type::

  sudo apt-get install python-virtualenv 

Let us now create an environment for kTBS::

  export DEST=/home/user/ktbs-env  # change the destination dir to your taste
  virtualenv "$DEST"
  source "$DEST/bin/activate"

The last line "activates" the environment, meaning that all commands related to Python packages will take effect in the ``ktbs-env`` environment rather than at the system level.

You now have two choices to install kTBS: `PyPI`__ and `git`__.

__ #installing-from-pypi
__ #installing-from-github

Installing from PyPI
~~~~~~~~~~~~~~~~~~~~

kTBS is available on the `PyPI <https://pypi.python.org/pypi/kTBS>`_,
the Python Package Index.
This allows you to easily install the latest stable version::

  pip install ktbs

This will install kTBS and all its dependencies.
If you further want to update it to the latest version, just type::

  pip install ktbs -U

You can now jump to `Running a standalone kTBS`_ or `Configuring Apache`_.

Installing from GitHub
~~~~~~~~~~~~~~~~~~~~~~

The source code of kTBS is hosted on GitHub_.
This allows you to get the latest developer version.
For this, you need to have `Git <http://git-scm.com/>`_ installed;
if you don't, type::

  sudo apt-get install git

Then, to retrieve kTBS, type::

  cd "$DEST"
  git clone https://github.com/ktbs/ktbs.git

You now have the source tree in ``$DEST/ktbs``.
You need to install the dependencies of kTBS; this is done with

  pip install -r "$DEST/ktbs/requirements.txt"

If you plan to be `Running a standalone kTBS`_,
you also need to add the executable in your PATH::

  export PATH="$PATH:$DEST/ktbs/bin"

This is not necessary if you're going for `Configuring Apache`_.




Running a standalone kTBS
+++++++++++++++++++++++++

After following the steps in the `previous section <#installing-ktbs>`_, you should be able to run kTBS by simply typing::

  ktbs

Note that, by default, kTBS stores the trace bases in memory,
so they will not be retained after you stop kTBS.
To make the trace bases persistent, you need to configure a store;
this can be done with the ``-r`` option::

  ktbs -r <storename>

A directory named ``<storename>`` will be used to store the trace bases;
if it does not exist, it will be automatically created and initialized.

.. note::

  You must *not* create the directory for the store;
  if the directory already exists,
  kTBS will assume that it is correctly initialized,
  and fail if it is not the case (*e.g.* if it is empty).

There are a number of other options for configuring kTBS;
to display them with their documentation, type::

  ktbs --help



Configuring Apache
++++++++++++++++++

kTBS can be used behing an Apache HTTP server; this has a number of advantages:

* kTBS does not have to listen on a separate port;
* Apache takes care or running/restarting kTBS when needed;
* kTBS can benefit from the functionalities provided by Apache modules,
  for example HTTPS support or user authentication.

To communicate with Apache, kTBS uses the WSGI_ protocol, so you need to install the corresponding Apache module::

  sudo apt-get install libapache2-mod-wsgi

You also need to write a dedicated WSGI script that Apache will be able to call (this is nothing but a Python script, declaring a function called ``application`` complying with the WSGI interface). An example of such a script is provided in the kTBS source tree at ``examples/wsgi/application.wsgi``. It is also available `online <https://raw.github.com/ktbs/ktbs/develop/examples/wsgi/application.wsgi>`_. At the top of the file are a few constants that you have to adapt to your own configuration.

Then, you need to change the apache configuration file; this would typically be ``/etc/apache2/sites-available/default`` or ``/etc/apache2/sites-available/default-ssl``. Those changes are twofold.

Just before the line ``</VirtualHost>`` add the following lines::

    <IfModule mod_wsgi.c>
        WSGIScriptAliasMatch ^/ktbs/.* /home/user/ktbs-env/application.wsgi
        WSGIDaemonProcess myktbs processes=1 threads=1 python-path=/home/user/ktbs-env/ktbs/lib
        WSGIProcessGroup myktbs
    </IfModule>

and at the end of the file, add the following lines::

    <IfModule mod_wsgi.c>
        WSGIPythonHome /home/user/ktbs-env
        WSGIPythonPath /home/user/ktbs-env/ktbs/lib
    </IfModule>

The configuration above may require some adaptation.
Specifically, it assumes that:

* you want the URL of your kTBS look like ``http://your.server.name/ktbs/``\ ; if you want to publish it at a different URL path [#]_, change the first argument of ``WSGIScriptAlias`` accordingly;

* you WSGI script is named ``/home/user/ktbs-env/application.wsgi``; if you named it otherwised and/or stored it elsewhere, change the second argument of ``WSGIScriptAlias`` accordingly;

* your Python virtual environment is in ``/home/user/ktbs-env``; if it has a different name, change all occurences of that path accordingly.

.. note::

    In the apache configuration above,
    the directory ``/home/user/ktbs-env/ktbs/lib`` is added to the python path
    (in two places).
    This is only required if you installed kTBS from GitHub,
    but it does no harm if you installed it from PyPI.

For more information on the WSGI directives,
see the `mod_wsgi documentation <https://code.google.com/p/modwsgi/wiki/ConfigurationGuidelines>`_.

.. TODO::

    Explain how to:

    * configure password authentication for kTBS,
    * configure give different permissions to differenc trace bases,
    * configure several kTBS in the same VirtualHost.

.. rubric:: Notes

.. [#] a tutorial for installing Python and Virtualenv on Windows is available
       at http://www.tylerbutler.com/2012/05/how-to-install-python-pip-and-virtualenv-on-windows-with-powershell/

.. [#] the protocol, server name and port number depend on the enclosing ``VirtualHost`` directive


.. _Apache: http://httpd.apache.org/
.. _Ubuntu server: http://www.ubuntu.com/download/server
.. _Python: http://python.org/
.. _Virtualenv: http://www.virtualenv.org/
.. _GitHub: https://github.com/ktbs/ktbs
.. _WSGI: http://wsgi.org/

