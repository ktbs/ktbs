Installing kTBS behing an Apache HTTP server
============================================

kTBS can be used behing an Apache HTTP server; this has a number of advantages:

* kTBS does not have to listen on a separate port;
* Apache takes care or running/restarting kTBS when needed;
* kTBS can benefit from the functionalities provided by Apache modules, for example HTTPS support or user authentication.

To communicate with Apache, kTBS uses the WSGI_ protocol, so you need to install the corresponding Apache module.

.. code-block:: bash

    $ sudo apt-get install libapache2-mod-wsgi

You also need to write a dedicated WSGI script that Apache will be able to call (this is nothing but a Python script, declaring a function called ``application`` complying with the WSGI interface). An example of such a script is provided in the kTBS source tree at ``examples/wsgi/application.wsgi``. It is also available `online <https://raw.github.com/ktbs/ktbs/develop/examples/wsgi/application.wsgi>`_. You must copy it together with its companion file `application.wsgi.conf <https://raw.github.com/ktbs/ktbs/develop/examples/wsgi/application.wsgi.conf>`_ which you need to adapt to your own configuration.

Then, you need to change the apache configuration file; this would typically be ``/etc/apache2/sites-available/default`` or ``/etc/apache2/sites-available/default-ssl``. Those changes are twofold.

Just before the line ``</VirtualHost>`` add the following lines:

.. code-block:: apache

    <IfModule mod_wsgi.c>
        WSGIScriptAlias /ktbs /home/user/ktbs-env/application.wsgi
        WSGIDaemonProcess myktbs processes=1 threads=2 python-path=/home/user/ktbs-env/ktbs/lib
        WSGIProcessGroup myktbs
    </IfModule>

and at the end of the file (you can adjust the number of threads to your needs), add the following lines:

.. code-block:: apache

    <IfModule mod_wsgi.c>
        WSGIPythonHome /home/user/ktbs-env
        WSGIPythonPath /home/user/ktbs-env/ktbs/lib
    </IfModule>

The configuration above may require some adaptation. Specifically, it assumes that:

* you want the URL of your kTBS look like ``http://your.server.name/ktbs/``\ ; if you want to publish it at a different URL path [#]_, change the first argument of ``WSGIScriptAlias`` accordingly;

* you WSGI script is named ``/home/user/ktbs-env/application.wsgi``; if you named it otherwised and/or stored it elsewhere, change the second argument of ``WSGIScriptAlias`` accordingly;

* your Python virtual environment is in ``/home/user/ktbs-env``; if it has a different name, change all occurences of that path accordingly.

.. note::

    In the apache configuration above, the directory ``/home/user/ktbs-env/ktbs/lib`` is added to the python path
    (in two places).
    This is only required if you installed kTBS from GitHub, but it does no harm if you installed it from PyPI.

For more information on the WSGI directives, see the `mod_wsgi documentation <https://code.google.com/p/modwsgi/wiki/ConfigurationGuidelines>`_.

Restricting access to kTBS
~~~~~~~~~~~~~~~~~~~~~~~~~~

Traces can contain very sensitive information, so you will probably want to restrict access to your kTBS.  To do this, you will need to add the following section to your Apache configuration files:

.. code-block:: apache

    <Location /ktbs>
        # here some access control directives
    </Location>

where ``/ktbs`` is the ``WSGIScriptAlias`` that you chose (see above).  To do this, you can either use Apache's authorization mechanisms, or use some kTBS plugin (to come).

Managing access control with Apache
```````````````````````````````````

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
`````````````````````````````````````````

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

.. rubric:: Notes

.. [#] the protocol, server name and port number depend on the enclosing ``VirtualHost`` directive

.. _WSGI: http://wsgi.org/
