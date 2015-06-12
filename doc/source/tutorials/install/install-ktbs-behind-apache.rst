Installing kTBS behing an Apache HTTP server
============================================

kTBS can be used behing an Apache HTTP server, this has a number of advantages:

* kTBS does not have to listen on a separate port,
* Apache takes care or running/restarting kTBS when needed,
* kTBS can benefit from the functionalities provided by Apache modules, for example **HTTPS support** or **user authentication**.

To communicate with Apache, kTBS uses the WSGI_ interface, so you need to install the corresponding Apache module: `mod_wsgi <https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide>`_.

Python Web Server Gateway Interface (WSGI)
++++++++++++++++++++++++++++++++++++++++++

The Python Web Server Gateway Interface (WSGI) is a Python **standard** which proposes a simple and universal interface between web servers and web applications or frameworks.

.. image:: server-app.png
    :width: 25em

*Image from Ian Bicking "WSGI a series of tubes" presentation*

Installing and configuring Apache mod_wsgi
++++++++++++++++++++++++++++++++++++++++++

Installing mod_wsgi
~~~~~~~~~~~~~~~~~~~

The simplest way is to use the system package manager.

.. code-block:: bash

    $ sudo apt-get install libapache2-mod-wsgi

.. Note::

    When using the module packaged in the system, it is linked to a given Python version but it does not matter for the current version of kTBS.

    This limitation can be solved using the new `mod_wsgi-express <http://blog.dscpl.com.au/2015/04/introducing-modwsgi-express.html>`_ project.
 
Creating a kTBS WSGI application interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apache needs to be able to **call kTBS** through a `WSGI application interface <http://webpython.codepoint.net/wsgi_application_interface>`_ that is just a **Python script** declaring a function called ``application`` which must be compliant to this specified interface.

That script is provided in the kTBS source tree [1]_ at ``examples/wsgi/application.wsgi``. 

.. literalinclude:: ../../../../examples/wsgi/application.wsgi
    :language: python
    :emphasize-lines: 22,30

As indicated in the header, this script is supposed to be used **as is** and should not be modified: customization is performed through a :ref:`ktbs-configuration-file`.

An example is provided in the kTBS source tree [1]_ at ``examples/wsgi/application.wsgi.conf``. Don't forget to adapt it to your own configuration.

.. literalinclude:: ../../../../examples/wsgi/application.wsgi.conf
    :language: ini

.. warning::

    The WSGI application will be run **as the user that Apache runs as**. As such, the user that Apache runs as **must have read access** to both the WSGI application script file and all the parent directories that contain it [2]_.

Configuring Apache 
~~~~~~~~~~~~~~~~~~

Once the WSGI application interface script is done, you need to add some mod_wsgi directives to Apache configuration files.

On Debian-Ubuntu, this would typically be in ``/etc/apache2/sites-available/default`` or ``/etc/apache2/sites-available/default-ssl`` for https configuration.

For a server configuration, we have assumed that you have followed :doc:`Installing a local kTBS <install-local-ktbs>` but we strongly advise you to use the ``/opt`` folder instead of the ``/home/user`` folder.

**Inside** the ``<VirtualHost xxx>`` directive, add the following lines (you can adjust the number of threads to your needs) :

.. code-block:: apache

    <IfModule mod_wsgi.c>
        WSGIScriptAlias /ktbs /opt/ktbs-env/application.wsgi
        WSGIDaemonProcess myktbs processes=1 threads=2 display-name=myktbs python-path=/opt/ktbs-env/ktbs/lib
        WSGIProcessGroup myktbs
    </IfModule>

**and at the end of the file** outside the VirtualHost directive, add the following lines:

.. code-block:: apache

    <IfModule mod_wsgi.c>
        WSGIPythonHome /opt/ktbs-env
        WSGIPythonPath /opt/ktbs-env/ktbs/lib
    </IfModule>

The configuration above may require some adaptation. Specifically, it assumes that:

* you want the URL of your kTBS look like ``http://your.server.name/ktbs/``\ ; if you want to publish it at a different URL path [3]_, change the first argument of ``WSGIScriptAlias`` accordingly;

* you WSGI script is named ``/opt/ktbs-env/application.wsgi``; if you named it otherwised and/or stored it elsewhere, change the second argument of ``WSGIScriptAlias`` accordingly;

* your Python virtual environment is in ``/opt/ktbs-env``; if it has a different name, change all occurences of that path accordingly.

.. note::

    In the apache configuration above, the directory ``/opt/ktbs-env/ktbs/lib`` is added to the python path
    (in two places).
    This is only required if you installed kTBS from GitHub, but it does no harm if you installed it from PyPI.

For a detailed information on the WSGI directives, please refer to the mod_wsgi documentation [2]_.

Restricting access to kTBS
++++++++++++++++++++++++++

Traces can contain very sensitive information, so you will probably want to restrict access to your kTBS.  To do this, you will need to add the following section to your Apache configuration files:

.. code-block:: apache

    <Location /ktbs>
        # here some access control directives
    </Location>

where ``/ktbs`` is the ``WSGIScriptAlias`` that you chose (see above).  To do this, you can either use Apache's authorization mechanisms, or use some kTBS plugin (to come).

Managing access control with Apache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apache provides `a number of directives`__ that you can use inside the ``Location`` section to restrict access based on various authorization schemes.

__ https://httpd.apache.org/docs/2.4/howto/access.html

If you want fine grained access control (on a per Base or per Trace basis), you can do this by adding further ``Location`` directives, for example:

.. code-block:: apache

    <Location /ktbs>
        # ... # global access control rules
    </Location>

    <Location /ktbs/base1/>
        # ... # access control for Base base1/
    </Location>

    <Location /ktbs/base1/t1/>
        # ... # access control for Trace base1/t1/
    </Location>

    <Location /ktbs/base2/>
        # ... # access control for Base base2/
    </Location>

.. warning::

   Note that `access control in Apache 2.2`__ differs significantly from Apache 2.4, so check your version and use the appropriate documentation.

__ https://httpd.apache.org/docs/2.2/howto/access.html

Managing access control with kTBS plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``authx`` plugin handles authentication (based on OAuth2) and authorization.

Eventually, kTBS may provide more such plugins.

Note that, whenever you want to use HTTP authentication with such a plugin, you will need the following directive:

.. code-block:: apache

    <Location /ktbs>
        WSGIPassAuthorization On
    </Location>

----

.. TODO::

    Explain how to:

    * configure several kTBS in the same VirtualHost.

Troubleshooting
+++++++++++++++

Does my Apache WSGI work ?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the basic ``examples/wsgi/hello.wsgi`` script provided in the kTBS source tree [1]_ as WSGI application interface to check that Apache WSGI correctly works.

.. literalinclude:: ../../../../examples/wsgi/hello.wsgi
    :language: python
    :emphasize-lines: 1

Replace the ``WSGIScriptAlias`` WSGI directive to point to this ``hello.wsgi`` script.

.. code-block:: apache
    :emphasize-lines: 4

    <VirtualHost *:80>

        <IfModule mod_wsgi.c>
            WSGIScriptAlias /ktbs /opt/ktbs-env/hello.wsgi
            WSGIDaemonProcess myktbs processes=1 threads=2 python-path=/opt/ktbs-env/ktbs/lib
            WSGIProcessGroup myktbs
        </IfModule>

.. rubric:: Notes

.. [1] https://github.com/ktbs/ktbs
.. [2] https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide
.. [3] the protocol, server name and port number depend on the enclosing ``VirtualHost`` directive


.. _WSGI: http://webpython.codepoint.net/wsgi_tutorial

