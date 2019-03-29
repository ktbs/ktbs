Installing kTBS behind an Nginx HTTP server
===========================================

`Unlike Apache <install-ktbs-behind-apache>`:doc:, Nginx does not supports the WSGI_ protocol.
As a consequence, Nginx must be configured as a *proxy*.

.. _Unlike Apache: 
.. _WSGI: http://wsgi.org/

Nginx configuration
+++++++++++++++++++

Here is an example Nginx configuration file:

.. code-block:: nginx

  server {
          server_name your.domain.com;
          listen 443;
          ssl on;
          # ... other parameters

          location /path/to/ktbs {
              proxy_pass http://localhost:8002/;
          }
  }

assuming that kTBS is running on the same server, and listening on port 8002 (see below).

kTBS configuration
++++++++++++++++++

kTBS must be run independantly, listening on a local port.
It must also be aware of the public URI underwhich it is published
(in the example above: `https://your.domain.com/path/to/ktbs/`).
This is achieved with the followin configuration directives:

.. code-block:: ini

  [server]
  scheme = http
  host-name = localhost
  port = 8002

  fixed-root-uri = https://your.domain.com/path/to/ktbs/

Alternative
+++++++++++

As an alternative, Nginx can also be run as a proxy in front of `uWSGI <install-ktbs-behind-uwsgi>`:doc:.