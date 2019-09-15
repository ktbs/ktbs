Installing kTBS behing an Apache HTTP server
============================================

Apache can be used as a proxy in front of a running instance of kTBS.
This has a number of advantages:

* adds HTTPS support;
* allows kTBS to co-exist with other services under the same domain name and port number;
* allows to add access control.

kTBS configuration
++++++++++++++++++

kTBS must first be `installed <install-local-ktbs>`:doc: 
and run independently, listening on a local port.
It must also be aware of the public URI under which it is published
(in the example above: `https://your.domain.com/path/to/ktbs/`).
This is achieved with the following configuration directives:

.. code-block:: ini

  [server]
  scheme = http
  host-name = localhost
  port = 8002

  fixed-root-uri = https://your.domain.com/path/to/ktbs/


Apache configuration
++++++++++++++++++++

A dedicated configuation file can be created,
typically in ``/etc/apache2/conf.d``,
with the following directives:

.. code-block:: apache

    # file: /etc/apache2/conf.d/ktbs.conf

    <Location /path/to/ktbs/>
        ProxyPass http://localhost:8002/
        ProxyPassReverse http://localhost:8002/
    </Location>

This configuration requires that Apache modules ``proxy`` and ``proxy_http`` are enabled;
this can be ensured with:

.. code-block:: bash

    $ a2enmod proxy proxy_http

Then Apache must be restarted to load the new configuration file:

.. code-block:: bash

    $ apache2ctl graceful


Restricting access to kTBS with Apache
++++++++++++++++++++++++++++++++++++++

Traces can contain very sensitive information, so you will probably want to restrict access to your kTBS. To do this, you will need to add some **access control directives** to the Apache configuration file described above.

For the following examples, we use the htpasswd_ utility provided with Apache to create (``-c``) a **password file** that will be used as source for `Apache authentication`_.

.. code-block:: bash
    :emphasize-lines: 2

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

In order to restrict access to kTBS as a whole,
the Apache configuration file above can be augmented to restrict access to kTBS, as illustrated below.

.. code-block:: apache
    :emphasize-lines: 5-9

    <Location /path/to/ktbs/>
        ProxyPass http://localhost:8002/
        ProxyPassReverse http://localhost:8002/

        AuthType Basic
        AuthName "kTBS"
        AuthBasicProvider file
        AuthUserFile /path/to/ktbs-users
        Require valid-user
    </Location>

Finer-grain restriction
~~~~~~~~~~~~~~~~~~~~~~~

It might be tempting to define finer-grained ACL through multiple ``Location`` directives,
to allow different users to access different part of your kTBS.
Note however the following drawbacks:

* kTBS is not aware of these different ACL,
  and it may leak some information from one user to another one;
* when the structure of your trace bases changes in kTBS,
  you must reflect the changes in the Apache configuration.

Eventually, kTBS will provide its own authorization mechanisms,
making this workaround moot.



What about mod_wsgi?
++++++++++++++++++++

``mod_wsgi`` is an Apache module dedicated to hosting Python WSGI_ applications entirely in Apache. In previous versions of kTBS, this was the recommended method for integrating with Apache.

The problem with ``mod_wsgi`` is that it must be compiled with the exact same version of Python as the one used by kTBS. Not only is it a problem if your distribution does not have the correct version of ``mod_wsgi``, but it also prevents using different applications based on different versions of Python in the same Apache instance.

.. _WSGI: http://webpython.codepoint.net/wsgi_tutorial
.. _`Apache authentication`: https://httpd.apache.org/docs/2.4/en/howto/auth.html
.. _htpasswd: https://httpd.apache.org/docs/2.4/programs/htpasswd.html
