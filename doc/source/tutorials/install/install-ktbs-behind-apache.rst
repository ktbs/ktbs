Installing kTBS behing an Apache HTTP server
============================================

kTBS can be used behing an Apache HTTP server, this has a number of advantages:

* kTBS does not have to listen on a separate port,
* Apache takes care or running/restarting kTBS when needed,
* kTBS can benefit from the functionalities provided by Apache modules, for example **HTTPS support** or **user authentication**.

To communicate with Apache, kTBS uses the WSGI_ interface, so you need to install the corresponding Apache module: `mod_wsgi <https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide>`_.

Python Web Server Gateway Interface (WSGI)
++++++++++++++++++++++++++++++++++++++++++

The Python Web Server Gateway Interface (WSGI_) is a **Python standard** [1]_ which proposes a simple and universal interface between web servers and web applications or frameworks.

.. image:: server-app.png
    :width: 25em

*Image from Ian Bicking "WSGI a series of tubes" presentation*

Installing and configuring Apache mod_wsgi
++++++++++++++++++++++++++++++++++++++++++

Installing mod_wsgi
~~~~~~~~~~~~~~~~~~~

The simplest way is to use the system package manager, the module is automatically enabled in Apache.

.. code-block:: bash

    $ sudo apt-get install libapache2-mod-wsgi

.. Note::

    When using the module packaged in the system, it is linked to a given Python version but it does not matter for the current version of kTBS. This limitation can be solved using the new `mod_wsgi-express <http://blog.dscpl.com.au/2015/04/introducing-modwsgi-express.html>`_ project.
 
Creating a kTBS WSGI application interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apache needs to be able to **call kTBS** through a `WSGI application interface`_ - that is just a **Python script** declaring a function called ``application`` which must be compliant to this specified interface.

That script is provided in the kTBS source tree [2]_ at ``examples/wsgi/application.wsgi``. 

.. literalinclude:: ../../../../examples/wsgi/application.wsgi
    :language: python
    :emphasize-lines: 22,30

As indicated in the header, this script is supposed to be used **as is** and should not be modified: customization is performed through a :ref:`ktbs-configuration-file`.

A configuration file example is provided in the kTBS source tree [2]_ at ``examples/wsgi/application.wsgi.conf``. Don't forget to adapt it to your own configuration.

.. literalinclude:: ../../../../examples/wsgi/application.wsgi.conf
    :language: ini

.. warning::

    The WSGI application will be run **as the user that Apache runs as**. As such, the user that Apache runs as **must have read access** to both the WSGI application script file and all the parent directories that contain it [3]_.

Configuring Apache 
~~~~~~~~~~~~~~~~~~

Once the `WSGI application interface`_ script is done, you need to add some mod_wsgi directives [4]_ to Apache configuration files.

On Debian-Ubuntu, this would typically be in ``/etc/apache2/sites-available/default`` (or ``/etc/apache2/sites-available/default-ssl`` for https configuration).

For a server configuration, we strongly advise you to use the ``/opt`` folder instead of the ``/home/user`` when installing kTBS using :doc:`Installing a local kTBS <install-local-ktbs>` procedure.

.. hint::

    It is advised to avoid using home directory because any misconfiguration of Apache could end up exposing your whole account for downloading [3]_.

**Inside** the ``<VirtualHost xxx>`` Apache directive, add the following lines :

.. code-block:: apache

    <IfModule mod_wsgi.c>
        WSGIScriptAlias /ktbs /opt/ktbs-env/application.wsgi
        WSGIDaemonProcess myktbs processes=1 threads=2 display-name=myktbs python-path=/opt/ktbs-env/ktbs/lib
        WSGIProcessGroup myktbs
    </IfModule>

and at the end of the file, **outside the** ``<VirtualHost xxx>`` **Apache directive**, add the following lines:

.. code-block:: apache

    <IfModule mod_wsgi.c>
        WSGIPythonHome /opt/ktbs-env
        WSGIPythonPath /opt/ktbs-env/ktbs/lib
    </IfModule>

The configuration above may require some adaptation :

- WSGIScriptAlias_ will map ``/ktbs`` URL to the ``/opt/ktbs-env/application.wsgi`` WSGI script ; 
  
  - if you want to publish it at a different URL path [5]_, change the first argument of WSGIScriptAlias_ accordingly; 
  - if you named your WSGI script otherwise and/or stored it elsewhere, change the second argument of WSGIScriptAlias_ accordingly;

- WSGIDaemonProcess_ and WSGIProcessGroup_ define a Process_group_ that mod_wsgi uses to manages this group of WSGI applications ; 
  
  - you can adjust the number of threads to your needs in WSGIDaemonProcess_ directive ;

- It assumes that your Python virtual environment is in ``/opt/ktbs-env``; if it has a different name, change all occurences of that path accordingly

For a detailed information on the WSGI directives, please refer to the mod_wsgi documentation [4]_.

.. note::

    In the apache configuration above, the directory ``/opt/ktbs-env/ktbs/lib`` is added to the python path
    (in two places).
    This is only required if you installed kTBS from GitHub, but it does no harm if you installed it from PyPI.

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

.. TODO::

    Explain how to:

    * configure several kTBS in the same VirtualHost.

Troubleshooting
+++++++++++++++

Does my Apache WSGI work ?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the basic ``examples/wsgi/hello.wsgi`` script provided in the kTBS source tree [2]_ as WSGI application interface to check that Apache WSGI correctly works.

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

Do not use mod_python and mod_wsgi on the same server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is because mod_python will in that case be responsible for initialising the Python interpreter, thereby overriding what mod_wsgi is trying to do. For best results, you should therefore use only mod_wsgi and not try and use mod_python on the same server at the same time [6]_.

Check Python version
~~~~~~~~~~~~~~~~~~~~

Check that Python 2.7 is used for main Python, python-dev, virtualenv and mod_wsgi.

.. rubric:: Notes

.. [1] see Python Enhancement Proposals 333 and 3333: https://www.python.org/dev/peps/pep-0333/, https://www.python.org/dev/peps/pep-3333/
.. [2] https://github.com/ktbs/ktbs
.. [3] https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide
.. [4] https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives
.. [5] the protocol, server name and port number depend on the enclosing ``VirtualHost`` directive
.. [6] https://code.google.com/p/modwsgi/wiki/VirtualEnvironments


.. _WSGI: http://webpython.codepoint.net/wsgi_tutorial
.. _`WSGI application interface`: http://webpython.codepoint.net/wsgi_application_interface
.. _WSGIScriptAlias: https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIScriptAlias
.. _WSGIDaemonProcess: https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIDaemonProcess 
.. _WSGIProcessGroup: https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIProcessGroup
.. _Process_group: https://en.wikipedia.org/wiki/Process_group
