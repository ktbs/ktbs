Installing kTBS behing an Apache HTTP server
============================================

kTBS can be used behing an Apache HTTP server, this has a number of advantages:

* kTBS does not have to listen on a separate port,
* Apache takes care or running/restarting kTBS when needed,
* kTBS can benefit from the functionalities provided by Apache modules,
  for example **HTTPS support** or **user authentication**.

To communicate with Apache, kTBS uses the WSGI_ interface [1]_,
so you need to install the corresponding Apache module:
`mod_wsgi <https://modwsgi.readthedocs.io/>`_.


Installing and configuring Apache mod_wsgi
++++++++++++++++++++++++++++++++++++++++++

Installing mod_wsgi
~~~~~~~~~~~~~~~~~~~

The simplest way is to use the system package manager:

.. code-block:: bash

    $ sudo apt-get install libapache2-mod-wsgi-py3

Then, to enable the `mod_wsgi` module in Apache:

.. code-block:: bash

    $ sudo a2enmod wsgi
 
Preparing kTBS WSGI application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will need to follow the tutorials for
`installing the released version <install-local-ktbs>`:doc:
or `the developper version <install-ktbs-dev-version>`:doc: of kTBS.
Note however that, for a server configuration,
you should use the ``/opt`` folder instead of ``/home/user``.
Otherwise, any misconfiguration of Apache could end up exposing your whole account for downloading [3]_.

You must then add two files in the ``/opt/ktbs-env`` folder,
to allow Apache to run kTBS through the `WSGI application interface`_,
a WSGI script and a configuration file.


The WSGI script is provided in the kTBS source tree [2]_
at ``examples/wsgi/application.wsgi``, and must be used *as is*,
without any modification.

An example :ref:`ktbs-configuration-file` is also provided in the source tree,
at ``examples/wsgi/application.wsgi.conf``.
You need to adapt it to your configuration,
at least the highlighted lines below.

.. literalinclude:: ../../../../examples/wsgi/application.wsgi.conf
    :language: ini
    :emphasize-lines: 5,6,9,10

.. hint::

    If you chose to rename the WSGI script,
    you must rename the configuration file accordingly,
    as the script locates the configuration file based on its own name.

.. warning::

    The WSGI application will be run **as the user that Apache runs as**
    (typically ``www-data`` on a Debian/Ubuntu system).
    As such, that user **must have read access** to the WSGI application script file,
    to all the parent directories that contain it and to the rdf database [3]_.


Configuring Apache
~~~~~~~~~~~~~~~~~~

Once the `WSGI application interface`_ script is done,
you need to add some mod_wsgi directives [4]_ to Apache configuration files.

On Debian-Ubuntu,
this would typically be in a new a file created in ``/etc/apache2/conf.d/``
(for example, ``/etc/apache2/conf.d/ktbs.conf``)

.. code-block:: apache

    <IfModule mod_wsgi.c>
        WSGIScriptAlias /ktbs /opt/ktbs-env/application.wsgi
        WSGIDaemonProcess myktbs processes=1 threads=4 python-home=/opt/ktbs-env display-name=myktbs maximum-requests=256
        <Location /ktbs>
            WSGIProcessGroup myktbs
        </Location>
    </IfModule>

The configuration above may require some adaptation :

- WSGIScriptAlias_ will map ``/ktbs`` URL to the ``/opt/ktbs-env/application.wsgi`` WSGI script ;

  - if you want to publish it at a different URL path [5]_,
    change the first argument of WSGIScriptAlias_ accordingly,
    as well as the argument of the inner Location directive;
  - if you named your WSGI script otherwise and/or stored it elsewhere,
    change the second argument of WSGIScriptAlias_ accordingly;

- WSGIDaemonProcess_ and WSGIProcessGroup_ define a Process_group_ that mod_wsgi uses to manages this group of WSGI applications ;

  - you can adjust the number of threads to your needs in WSGIDaemonProcess_ directive ;

- It assumes that your Python virtual environment is in ``/opt/ktbs-env``; if it has a different name, change all occurences of that path accordingly

For a detailed information on the WSGI directives, please refer to the mod_wsgi documentation [4]_.

Restricting access to kTBS with Apache
++++++++++++++++++++++++++++++++++++++

Traces can contain very sensitive information, so you will probably want to restrict access to your kTBS. To do this, you will need to add some **access control directives** to your Apache configuration files.

For the following examples, we use the htpasswd_ utility provided with Apache to create (``-c``) a **password file** that will be used as source for `Apache authentication`_.

.. code-block:: bash
    :emphasize-lines: 2

    $ cd /opt/ktbs-data
    $ htpasswd -c ktbs-users jdoe
    New password: 
    Re-type new password: 
    Adding password for user jdoe

Later on, you can add users to your password file with the same utility:

.. code-block:: bash

    $ htpasswd /opt/ktbs-data/ktbs-users aduran
    New password: 

Basic global restriction
~~~~~~~~~~~~~~~~~~~~~~~~

Assuming that ``/ktbs`` is the root url of your kTBS (as specified in the ``WSGIScriptAlias`` directive above), you can use a Location_ directive to require that access to kTBS is only granted to authenticated users configured in the password file:

.. code-block:: apache

    <Location /ktbs>
        AuthType Basic
        AuthName "Restricted area"
        AuthBasicProvider file
        AuthUserFile /opt/ktbs-data/ktbs-users
        Require valid-user
    </Location>

Restricting access only to obsel "viewing"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Still assuming that ``/ktbs`` is the root url of your kTBS, we use here the LocationMatch_ directive to set up different rules for kTBS root, bases and traces access than for obsels access. LocationMatch_ applies the enclosed directives to URLs matching the given "regular expressions".

.. note::

    This example was written before "sub-bases"
    (*i.e.* bases contained in other bases rather than the kTBS root)
    were supported.
    So the assumption is that any URL of depth 2 (below the kTBS root)
    identifies a *trace*.


The first group of directives let any user send GET and POST request to kTBS root, bases and traces. Any other HTTP request type, such as PUT or DELETE, is only allowed for user "jdoe" once authenticated.

The second group of directives let any user send GET requests to aspect resources of kTBS traces (`@obsels` and `@stats`). Any other HTTP request type, GET, POST or DELETE, is only allowed for user "jdoe" once authenticated. Thus the obsels can be viewed, by unauthenticated users, but only "jdoe" can modify them.

.. code-block:: apache

    <LocationMatch "^/(ktbs/|ktbs/.+/|ktbs/.+/.+/)$">
        AuthType Basic
        AuthName "Restricted area"
        AuthBasicProvider file
        AuthUserFile /opt/ktbs-data/ktbs-users

        <LimitExcept GET POST>
            Require user jdoe
        </LimitExcept>
    </LocationMatch>

    <LocationMatch "^/ktbs/.+/.+/@.+$">
        AuthType Basic
        AuthName "Restricted area"
        AuthBasicProvider file
        AuthUserFile /opt/ktbs-data/ktbs-users

        <LimitExcept GET>
            Require user jdoe
        </LimitExcept>
    </LocationMatch>


per Base or per Trace access control with Apache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to define access control on a per Base or per Trace basis, you can do this by adding several Location_ or LocationMatch_ directives using `various authorization schemes`_ that Apache provides. For example:

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

   Note that `access control in Apache 2.4`__ differs significantly from Apache 2.2, so check your version and use the appropriate documentation.

__ https://httpd.apache.org/docs/2.4/

Managing access control with kTBS plugins
+++++++++++++++++++++++++++++++++++++++++

The ``authx`` plugin handles authentication (based on OAuth2) and authorization.

Eventually, kTBS may provide more such plugins.

Note that, whenever you want to use HTTP authentication with such a plugin, you will need the mod_wsgi WSGIPassAuthorization_ directive:

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
    :emphasize-lines: 6

    <VirtualHost *:80>

        ...

        <IfModule mod_wsgi.c>
            WSGIScriptAlias /ktbs /opt/ktbs-env/hello.wsgi
            WSGIDaemonProcess myktbs processes=1 threads=2 python-home=/opt/ktbs-env/
            WSGIProcessGroup myktbs
        </IfModule>

        ...

Invalid data in the repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It may take some steps to tune kTBS configuration as you want (changing port, base-url, ...) and this may lead to store invalid data to kTBS repository if configured.

In that case try to remove the created repository, kTBS will create a new one.

Do not use mod_python and mod_wsgi on the same server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is because mod_python will in that case be responsible for initialising the Python interpreter, thereby overriding what mod_wsgi is trying to do. For best results, you should therefore use only mod_wsgi and not try and use mod_python on the same server at the same time [6]_.

Check Python version
~~~~~~~~~~~~~~~~~~~~

Check that the same version of Python 3.x is used for main Python, python-dev, virtualenv and mod_wsgi.

.. rubric:: Notes

.. [1] see Python Enhancement Proposals 333 and 3333: https://www.python.org/dev/peps/pep-0333/, https://www.python.org/dev/peps/pep-3333/
.. [2] https://github.com/ktbs/ktbs
.. [3] https://modwsgi.readthedocs.io/en/develop/user-guides/quick-configuration-guide.html
.. [4] https://modwsgi.readthedocs.io/en/develop/user-guides/configuration-guidelines.html#
.. [5] the protocol, server name and port number depend on the enclosing ``VirtualHost`` directive
.. [6] https://modwsgi.readthedocs.io/en/develop/user-guides/virtual-environments.html


.. _WSGI: http://webpython.codepoint.net/wsgi_tutorial
.. _`WSGI application interface`: http://webpython.codepoint.net/wsgi_application_interface
.. _WSGIScriptAlias: https://modwsgi.readthedocs.io/en/develop/configuration-directives/WSGIScriptAlias.html
.. _WSGIDaemonProcess: https://modwsgi.readthedocs.io/en/develop/configuration-directives/WSGIDaemonProcess.html
.. _WSGIProcessGroup: https://modwsgi.readthedocs.io/en/develop/configuration-directives/WSGIProcessGroup.html
.. _Process_group: https://en.wikipedia.org/wiki/Process_group
.. _`Apache authentication`: https://httpd.apache.org/docs/2.4/en/howto/auth.html
.. _htpasswd: https://httpd.apache.org/docs/2.4/programs/htpasswd.html
.. _Location: https://httpd.apache.org/docs/2.4/en/mod/core.html#location
.. _`various authorization schemes`: https://httpd.apache.org/docs/2.4/en/howto/access.html
.. _LocationMatch: https://httpd.apache.org/docs/2.4/en/mod/core.html#locationmatch
.. _WSGIPassAuthorization: https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIPassAuthorization
